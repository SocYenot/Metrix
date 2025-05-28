from django.urls import path
from .views import index, SignUpView, LoginView, research, LogoutView, \
    QuestionListView, AddQuestionView, ResearchCreateView, \
    ParticipantAddView, ResearchQuestionAddView, ResearchDetailView, ResearchConfirmView, \
    cancel_research_creation, ResearchDeleteView, QuestionUpdateView, QuestionDeleteView, \
    ConductTestView, test_redirect, TestCompletedView, AccountView, AccountDeleteView, AccountEditView
from . import views




urlpatterns = [
    path('', index, name='index'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('research/', research, name='research'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('questions/', QuestionListView.as_view(), name='question_list'),
    path('questions/add/', AddQuestionView.as_view(), name='question-add'),
    path('questions/<int:pk>/edit/', QuestionUpdateView.as_view(), name='question-edit'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question-delete'),
    path('research/add/', ResearchCreateView.as_view(), name='add-research'),
    path('research/<int:research_id>/delete/', ResearchDeleteView.as_view(), name='delete-research'),
    path('research/add/participants/', ParticipantAddView.as_view(), name='add-participants'),
    path('research/add/questions/', ResearchQuestionAddView.as_view(), name='add-research-questions'),
    path('research/<int:research_id>/', ResearchDetailView.as_view(), name='research-detail'),
    path('research/confirm/', ResearchConfirmView.as_view(), name='research-confirm'),
    path('research/cancel/', cancel_research_creation, name='cancel-research'),
    path('research/<int:pk>/test/', test_redirect),
    path('research/<int:pk>/test/<int:step>/', ConductTestView.as_view(), name='conduct-test'),
path('research/<int:pk>/test/completed/', TestCompletedView.as_view(), name='test-completed'),
path('participants/manage/', views.participant_manage_list, name='participant-manage-list'),
    path('participants/<int:pk>/edit/', views.participant_edit, name='participant-edit'),
path('participants/<int:pk>/', views.participant_detail, name='participant-detail'),
    path('account/', AccountView.as_view(), name='account'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
path('account/edit/', AccountEditView.as_view(), name='account-edit'),



]