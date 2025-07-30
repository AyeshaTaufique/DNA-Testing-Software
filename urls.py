from django.urls import path
from . import views





urlpatterns = [
    path('login/', views.login_chemist, name='login'),
    path('logout/', views.logout_chemist, name='logout'),
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chemist-profile/', views.chemist_profile, name='chemist_profile'),
    path('update-chemist-profile/', views.update_chemist_profile, name='update_chemist_profile'),
    path('add-profile/', views.add_profile, name='add_profile'),
    path('save-profile/', views.save_profile, name='save_profile'),
    path('get-dna-profiles/', views.get_dna_profiles, name='get_dna_profiles'),
    path('duo-test/', views.duo_test, name='duo_test'),
    path('trio-test/', views.trio_test, name='trio_test'),
    path('complex-test/', views.complex_test, name='complex_test'),
    path('kinship-analysis/', views.kinship_analysis, name='kinship_analysis'),
    path('sibship-analysis/', views.sibship_analysis, name='sibship_analysis'),
    path('profile-inclusion/', views.profile_inclusion, name='profile_inclusion'),
    path('random-match/', views.random_match, name='random_match'),
    path('report/', views.report, name='report'),


]

