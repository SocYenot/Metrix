from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.views.generic import CreateView, TemplateView
from django.views.generic.detail import DetailView
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.forms import formset_factory

from .models import *
from .forms import ResearchCreateForm, ParticipantForm, ResearchQuestionForm

from metrix.forms import CustomUserCreationForm, AddQuestionForm


# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect('research')
    return render(request, 'metrix/index.html')

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'metrix/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, 'Congratulations, you\'ve been successfully signed up!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Sadly, we couldn\'t sign you up!')
        return super().form_invalid(form)

class LoginView(auth_views.LoginView):
    template_name = 'metrix/login.html'

    success_url = reverse_lazy('research')
@login_required
def research(request):
    researches = Research.objects.filter(owner=request.user).order_by('-created_at')
    paginator = Paginator(researches, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'metrix/research.html', {'page_obj': page_obj})


@login_required
def cancel_research_creation(request):
    keys_to_clear = ['research_data', 'participants_data', 'questions_data']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    return redirect('research')
class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('index')


class AddQuestionView(LoginRequiredMixin, FormView):
    template_name = 'metrix/add_question.html'
    form_class = AddQuestionForm
    success_url = reverse_lazy('question_list')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class QuestionListView(LoginRequiredMixin, ListView):
    model = Question
    template_name = 'metrix/question_list.html'
    context_object_name = 'questions'
    ordering = ['-created_at']

class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    fields = ['text']
    template_name = 'metrix/question_edit.html'
    success_url = reverse_lazy('question_list')

class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question
    template_name = 'metrix/question_confirm_delete.html'
    success_url = reverse_lazy('question_list')

class ResearchDeleteView(LoginRequiredMixin, DeleteView):
    model = Research
    template_name = 'metrix/research_confirm_delete.html'
    pk_url_kwarg = 'research_id'
    success_url = reverse_lazy('research')

    def get_queryset(self):
        return Research.objects.filter(owner=self.request.user)
class ResearchCreateView(LoginRequiredMixin, FormView):
    form_class = ResearchCreateForm
    template_name = 'metrix/research_create.html'

    def get(self, request, *args, **kwargs):
        # Jeśli zaczynasz nowy proces tworzenia badania, czyść dane sesyjne
        keys_to_clear = ['research_data', 'participants_data', 'questions_data']
        for key in keys_to_clear:
            if key in request.session:
                del request.session[key]
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        return self.request.session.get('research_data', {})

    def form_valid(self, form):
        # Zapisz dane z pierwszego kroku do sesji
        self.request.session['research_data'] = form.cleaned_data
        self.request.session.modified = True
        # Przekieruj do dodawania uczestników
        return redirect('add-participants')

class ParticipantAddView(LoginRequiredMixin, View):
    def get(self, request):
        research_data = request.session.get('research_data')
        if not research_data:
            return redirect('add-research')

        person_count = research_data['person_count']

        # Pobierz dane z sesji lub stwórz listę pustych dictów o długości person_count
        initial_data = request.session.get('participants_data')
        if not initial_data or len(initial_data) != person_count:
            initial_data = [{} for _ in range(person_count)]

        ParticipantFormSet = formset_factory(ParticipantForm, extra=0)
        formset = ParticipantFormSet(initial=initial_data)

        return render(request, 'metrix/participant_add.html', {'formset': formset, 'research': research_data})

    def post(self, request):
        research_data = request.session.get('research_data')
        person_count = research_data['person_count']

        ParticipantFormSet = formset_factory(ParticipantForm, extra=0)
        formset = ParticipantFormSet(request.POST)

        if formset.is_valid():
            participants_data = [form.cleaned_data for form in formset]
            request.session['participants_data'] = participants_data
            request.session.modified = True
            return redirect('add-research-questions')

        return render(request, 'metrix/participant_add.html', {'formset': formset, 'research': research_data})


class ResearchQuestionAddView(LoginRequiredMixin, View):
    def get(self, request):
        research_data = request.session.get('research_data')
        if not research_data:
            return redirect('add-research')

        question_count = research_data['question_count']
        person_count = research_data['person_count']
        max_choices = person_count - 1

        initial_data = request.session.get('questions_data', [{}] * question_count)

        QuestionFormSet = formset_factory(ResearchQuestionForm, extra=0)
        formset = QuestionFormSet(initial=initial_data)

        # <- RĘCZNIE ustaw `max_choices` w każdym formularzu
        for form in formset:
            form.fields['choice_count'].max_value = max_choices
            form.fields['choice_count'].widget.attrs['max'] = max_choices

        return render(request, 'metrix/research_questions_add.html', {
            'formset': formset,
            'research': research_data
        })

    def post(self, request):
        research_data = request.session.get('research_data')
        if not research_data:
            return redirect('add-research')

        max_choices = research_data['person_count'] - 1
        QuestionFormSet = formset_factory(ResearchQuestionForm, extra=0)
        formset = QuestionFormSet(request.POST)

        if formset.is_valid():
            questions_data = []
            seen_question_ids = set()

            for form in formset:
                question_obj = form.cleaned_data.get('question')
                if not question_obj:
                    continue

                if question_obj.pk in seen_question_ids:
                    form.add_error('question', "This question has already been selected.")
                else:
                    seen_question_ids.add(question_obj.pk)

                choice_count = form.cleaned_data.get('choice_count')
                if choice_count is not None and choice_count > max_choices:
                    form.add_error('choice_count', f'Max allowed is {max_choices}.')

            # ponowne sprawdzenie czy po walidacji nadal jest OK
            if any(form.errors for form in formset):
                return render(request, 'metrix/research_questions_add.html', {
                    'formset': formset,
                    'research': research_data
                })

            # wszystko OK, zapisujemy do sesji
            for form in formset:
                question_obj = form.cleaned_data['question']
                questions_data.append({
                    'question_id': question_obj.pk,
                    'question_text': question_obj.text,
                    'choice_count': form.cleaned_data['choice_count']
                })

            request.session['questions_data'] = questions_data
            request.session.modified = True
            return redirect('research-confirm')

        return render(request, 'metrix/research_questions_add.html', {
            'formset': formset,
            'research': research_data
        })


class ResearchDetailView(LoginRequiredMixin, DetailView):
    model = Research
    template_name = 'metrix/research_detail.html'
    context_object_name = 'research'
    pk_url_kwarg = 'research_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        research = self.get_object()
        context['participants'] = Participant.objects.filter(research=research)
        context['questions'] = ResearchQuestion.objects.filter(research=research)
        return context

class ResearchConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'metrix/research_confirm.html'

    def get(self, request):
        research_data = request.session.get('research_data')
        participants_data = request.session.get('participants_data')
        questions_data = request.session.get('questions_data')

        if not (research_data and participants_data and questions_data):
            return redirect('research')

        context = {
            'research': research_data,
            'participants': participants_data,
            'questions': questions_data,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        research_data = request.session.get('research_data')
        participants_data = request.session.get('participants_data')
        questions_data = request.session.get('questions_data')

        if not (research_data and participants_data and questions_data):
            messages.error(request, "Incomplete data to save research.")
            return redirect('research')

        # Tworzymy Research w bazie
        research = Research.objects.create(
            owner=request.user,
            name=research_data['name'],
            person_count=research_data['person_count'],
            question_count=research_data['question_count']
        )

        # Tworzymy uczestników
        for pdata in participants_data:
            participant = Participant(
                research=research,
                **pdata
            )
            participant.save()

        # Tworzymy pytania
        for qdata in questions_data:
            question_instance = Question.objects.get(pk=qdata['question_id'])
            ResearchQuestion.objects.create(
                research=research,
                question=question_instance,
                choice_count=qdata['choice_count']
            )

        # Czyscimy sesję
        for key in ['research_data', 'participants_data', 'questions_data']:
            if key in request.session:
                del request.session[key]

        return redirect('/research/')
