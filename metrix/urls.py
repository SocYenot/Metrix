from django.urls import path
from .views import index, SignUpView, LoginView, research, LogoutView, \
    QuestionListView, AddQuestionView, ResearchCreateView, \
    ParticipantAddView, ResearchQuestionAddView, ResearchDetailView, ResearchConfirmView, \
    cancel_research_creation, ResearchDeleteView




urlpatterns = [
    path('', index, name='index'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('research/', research, name='research'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('questions/', QuestionListView.as_view(), name='question_list'),
    path('questions/add/', AddQuestionView.as_view(), name='question-add'),
    path('research/add/', ResearchCreateView.as_view(), name='add-research'),
    path('research/<int:research_id>/delete/', ResearchDeleteView.as_view(), name='delete-research'),
    path('research/add/participants/', ParticipantAddView.as_view(), name='add-participants'),
    path('research/add/questions/', ResearchQuestionAddView.as_view(), name='add-research-questions'),
    path('research/<int:research_id>/', ResearchDetailView.as_view(), name='research-detail'),
    path('research/confirm/', ResearchConfirmView.as_view(), name='research-confirm'),
    path('research/cancel/', cancel_research_creation, name='cancel-research'),


]