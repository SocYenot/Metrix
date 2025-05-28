from collections import defaultdict
from itertools import combinations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views, login, update_session_auth_hash, logout
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
from .forms import ResearchCreateForm, ParticipantForm, ResearchQuestionForm, ConductTestForm, EmailUpdateForm, \
    PasswordUpdateForm, UsernameUpdateForm

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

class AccountView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'metrix/account.html', {
            'user': request.user
        })


class AccountEditView(LoginRequiredMixin, View):
    def get(self, request):
        email_form = EmailUpdateForm(instance=request.user, prefix='email')
        username_form = UsernameUpdateForm(instance=request.user, prefix='username')
        password_form = PasswordUpdateForm(prefix='password')
        return render(request, 'metrix/account_edit.html', {
            'email_form': email_form,
            'username_form': username_form,
            'password_form': password_form,
        })

    def post(self, request):
        email_form = EmailUpdateForm(request.POST, instance=request.user, prefix='email')
        username_form = UsernameUpdateForm(request.POST, instance=request.user, prefix='username')
        password_form = PasswordUpdateForm(request.POST, prefix='password')

        if 'email-submit' in request.POST and email_form.is_valid():
            email_form.save()
            messages.success(request, "Email updated successfully.")
            return redirect('account-edit')

        elif 'username-submit' in request.POST and username_form.is_valid():
            username_form.save()
            messages.success(request, "Username updated successfully.")
            return redirect('account-edit')

        elif 'password-submit' in request.POST and password_form.is_valid():
            new_password = password_form.cleaned_data['password1']
            user = request.user
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated successfully.")
            return redirect('account-edit')

        return render(request, 'metrix/account_edit.html', {
            'email_form': email_form,
            'username_form': username_form,
            'password_form': password_form,
        })

class AccountDeleteView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'metrix/account_confirm_delete.html')

    def post(self, request):
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('index')

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pobierz ID pytań używanych w jakimkolwiek ResearchQuestion
        used_question_ids = ResearchQuestion.objects.values_list('question_id', flat=True).distinct()
        context['used_question_ids'] = set(used_question_ids)  # set dla szybszego sprawdzania w templatce

        return context


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

        participants = Participant.objects.filter(research=research)
        responses = Response.objects.filter(research=research).select_related('source', 'target', 'question')
        questions = ResearchQuestion.objects.filter(research=research).select_related('question')

        matrices = []
        for rq in questions:
            matrix = {
                'rq': rq,
                'question': rq.question,
                'data': []
            }

            for source in participants:
                row = []
                for target in participants:
                    match = responses.filter(question=rq.question, source=source, target=target).exists()
                    row.append(match)
                matrix['data'].append({'source': source.name, 'row': row})
            matrices.append(matrix)

        context['questions'] = list(questions)
        context['participants'] = participants
        context['matrices'] = matrices

        # OGÓLNE RELACJE (niezależnie od pytania)
        adjacency = defaultdict(set)
        for r in responses:
            adjacency[r.source].add(r.target)

        all_participants = list(participants)
        pairs, chains, stars, cliques = [], [], [], []

        for a in all_participants:
            for b in adjacency[a]:
                if a in adjacency[b] and a.pk < b.pk:
                    pairs.append((a, b))

        for a in all_participants:
            for b in adjacency[a]:
                if a not in adjacency[b]:
                    for c in adjacency[b]:
                        if b not in adjacency[c] and c != a:
                            chains.append((a, b, c))

        threshold = len(participants) // 2
        for p in all_participants:
            incoming = sum(1 for others in adjacency.values() if p in others)
            outgoing = len(adjacency[p])
            if incoming >= threshold and outgoing == 0:
                stars.append(p)

        for combo in combinations(all_participants, 3):
            a, b, c = combo
            if (b in adjacency[a] and c in adjacency[a] and
                    a in adjacency[b] and c in adjacency[b] and
                    a in adjacency[c] and b in adjacency[c]):
                cliques.append(combo)

        network = all(all(p2 in adjacency[p1] or p1 == p2 for p2 in all_participants) for p1 in all_participants)

        context['relations'] = {
            'pairs': pairs,
            'chains': chains,
            'stars': stars,
            'cliques': cliques,
            'network': network,
        }

        # RELACJE I WSKAŹNIKI PER PYTANIE
        relations_by_question = {}
        group_metrics_by_question = {}
        individual_metrics_by_question = {}

        for rq in questions:
            question = rq.question
            q_responses = responses.filter(question=question)
            adjacency = defaultdict(set)
            incoming_count = defaultdict(int)

            for r in q_responses:
                adjacency[r.source].add(r.target)
                incoming_count[r.target] += 1

            all_participants = list(participants)
            mutual_count = 0
            unreciprocated_count = 0

            # Pary
            pairs = []
            for a in all_participants:
                for b in adjacency[a]:
                    if a in adjacency[b] and a.pk < b.pk:
                        pairs.append((a, b))
                        mutual_count += 1

            # Łańcuchy
            chains = []
            for a in all_participants:
                for b in adjacency[a]:
                    if a not in adjacency[b]:
                        for c in adjacency[b]:
                            if b not in adjacency[c] and c != a:
                                chains.append((a, b, c))

            # Gwiazdy – osoby z największą liczbą wskazań (incoming votes)
            stars = []
            incoming_counts = {p: 0 for p in all_participants}
            for voters in adjacency.values():
                for voted in voters:
                    incoming_counts[voted] += 1
            if incoming_counts:
                max_incoming = max(incoming_counts.values())
                stars = [p for p, count in incoming_counts.items() if count == max_incoming and max_incoming > 0]

            # Kliki
            cliques = []
            for combo in combinations(all_participants, 3):
                a, b, c = combo
                if (b in adjacency[a] and c in adjacency[a] and
                        a in adjacency[b] and c in adjacency[b] and
                        a in adjacency[c] and b in adjacency[c]):
                    cliques.append(combo)

            # Sieć
            network = all(all(p2 in adjacency[p1] or p1 == p2 for p2 in all_participants) for p1 in all_participants)

            # **Tutaj klucze na question.pk zamiast question**
            relations_by_question[question.pk] = {
                'pairs': pairs,
                'chains': chains,
                'stars': stars,
                'cliques': cliques,
                'network': network,
            }

            # 🧮 Wskaźniki grupowe
            required_choices = rq.choice_count or 1  # zabezpieczenie
            participant_count = len(participants)
            max_mutual_possible = (required_choices * participant_count) / 2
            cohesion = mutual_count / max_mutual_possible if max_mutual_possible else 0

            for a in all_participants:
                for b in adjacency[a]:
                    if a not in adjacency[b]:
                        unreciprocated_count += 1

            denominator_density = unreciprocated_count * (
                    1 - (required_choices / (participant_count - 1))) if participant_count > 1 else 0
            numerator_density = mutual_count * (
                    1 - (required_choices / (participant_count - 1))) if participant_count > 1 else 0

            if denominator_density > 0:
                density = numerator_density / denominator_density
            elif numerator_density > 0:
                density = float('inf')  # unreciprocated == 0, mutual > 0
            else:
                density = 0

            non_isolated = sum(1 for p in participants if incoming_count[p] > 0)
            isolated = participant_count - non_isolated
            isolation = (1 / isolated) if isolated > 0 else 0

            group_metrics_by_question[question.pk] = {
                'cohesion': round(cohesion, 2),
                'density': round(density, 2) if density != float('inf') else '∞',
                'isolation': round(isolation, 2)
            }

            individual_status = {}
            for p in participants:
                status = incoming_count[p] / (participant_count - 1) if participant_count > 1 else 0
                individual_status[p] = round(status, 2)

            individual_metrics_by_question[question.pk] = individual_status

        context['relations_by_question'] = relations_by_question
        context['group_metrics_by_question'] = group_metrics_by_question
        context['individual_metrics_by_question'] = individual_metrics_by_question

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

        for key in ['research_data', 'participants_data', 'questions_data']:
            if key in request.session:
                del request.session[key]

        return redirect('/research/')

def test_redirect(request, pk):
    return redirect('conduct-test', pk=pk, step=0)
class ConductTestView(View):
    def get(self, request, pk, step=0):
        research = get_object_or_404(Research, pk=pk)
        participants_qs = research.participant_set.all()
        participants = list(participants_qs)

        if step >= len(participants):
            return redirect('test-completed', pk=pk)

        current_participant = participants[step]
        questions = ResearchQuestion.objects.filter(research=research)


        form = ConductTestForm(
            participant=current_participant,
            questions=questions,
            choices_queryset=participants_qs
        )

        return render(request, 'metrix/conduct_test.html', {
            'form': form,
            'participant': current_participant,
            'step': step,
            'total': len(participants),
            'research': research,
            'questions': questions,
            'participants': participants
        })

    def post(self, request, pk, step=0):
        research = get_object_or_404(Research, pk=pk)
        participants_qs = research.participant_set.all()
        participants = list(participants_qs)

        if step >= len(participants):
            return redirect('test-completed', pk=pk)

        current_participant = participants[step]
        questions = ResearchQuestion.objects.filter(research=research)

        form = ConductTestForm(
            request.POST,
            participant=current_participant,
            questions=questions,
            choices_queryset=participants_qs
        )

        if form.is_valid():
            for question in questions:
                selected_targets = form.cleaned_data.get(f"question_{question.id}", [])
                for target in selected_targets:
                    Response.objects.create(
                        research=research,
                        question=question.question,
                        source=current_participant,
                        target=target
                    )

            # 👇 Dopiero po zapisaniu ostatniego uczestnika ustawiamy is_completed
            if step + 1 >= len(participants):
                research.is_completed = True
                research.save()

            return redirect('conduct-test', pk=pk, step=step + 1)

        return render(request, 'metrix/conduct_test.html', {
            'form': form,
            'participant': current_participant,
            'step': step,
            'total': len(participants),
            'research': research,
            'questions': questions,
            'participants': participants
        })


class TestCompletedView(TemplateView):
    template_name = 'metrix/test_completed.html'

def participant_manage_list(request):
    participants = Participant.objects.all()
    return render(request, 'metrix/participants_manage.html', {'participants': participants})

def participant_edit(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            return redirect('participant-manage-list')
    else:
        form = ParticipantForm(instance=participant)
    return render(request, 'metrix/participant_edit.html', {'form': form, 'participant': participant})

def participant_detail(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    researches = [participant.research]
    return render(request, 'metrix/participant_detail.html', {
        'participant': participant,
        'researches': researches
    })