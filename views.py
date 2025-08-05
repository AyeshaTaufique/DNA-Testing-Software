
from django.shortcuts import render, redirect
from .forms import ChemistSignupForm, ChemistLoginForm
from .models import Chemist, DNAProfile, ProfileAllele,Test, TestProfile
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from frontend.calculations.rmp_test import run_rmp_analysis
from frontend.calculations.duo_test import run_duo_analysis
from frontend.calculations.trio_test import run_trio_analysis 

import json

# Landing Page
def index(request):
    return render(request, 'manage/index.html')

# Dashboard Page (Only visible when logged in)
def dashboard(request):
    if not request.session.get('chemist_id'):
        return redirect('login')
    chemist = Chemist.objects.get(id=request.session['chemist_id'])
    return render(request, 'manage/dashboard.html', {'chemist': chemist})

# Logout and clear session
from django.contrib.auth import logout

# Logout and clear session
def logout_chemist(request):
    request.session.clear()  # Clears all session data
    return redirect('login')


# Signup View
def signup(request):
    show_signup = False  # Default tab is login
    if request.method == 'POST':
        form = ChemistSignupForm(request.POST)
        if form.is_valid():
            chemist = form.save(commit=False)
            chemist.password = make_password(form.cleaned_data['password'])
            chemist.save()
            messages.success(request, "Signup successful. Please log in.")
            return redirect('signup')  # Show login after signup
        else:
            show_signup = True  # Show signup tab again if errors
    else:
        form = ChemistSignupForm()
    return render(request, 'manage/signup.html', {
        'form': form,
        'show_signup': show_signup,
        'login_form': ChemistLoginForm()
    })

# Login View
def login_chemist(request):
    show_signup = False
    if request.method == 'POST':
        form = ChemistLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                chemist = Chemist.objects.get(email=email)
                if check_password(password, chemist.password):
                    request.session['chemist_id'] = chemist.id
                    return redirect('dashboard')
                else:
                    messages.error(request, "Incorrect password.")
            except Chemist.DoesNotExist:
                messages.error(request, "Email not found. Please sign up first.")
                show_signup = True
    else:
        form = ChemistLoginForm()
    return render(request, 'manage/signup.html', {
        'form': ChemistSignupForm(),
        'login_form': form,
        'show_signup': show_signup
    })


# Chemist Profile View
def chemist_profile(request):
    if not request.session.get('chemist_id'):
        return redirect('login')
    chemist = Chemist.objects.get(id=request.session['chemist_id'])
    return render(request, 'manage/chemist_profile.html', {'chemist': chemist})

# Profile Update Logic
@csrf_exempt
def update_chemist_profile(request):
    if not request.session.get('chemist_id'):
        return redirect('login')

    chemist = Chemist.objects.get(id=request.session['chemist_id'])

    if request.method == 'POST':
        updated_name = request.POST.get('name', '').strip()
        updated_designation = request.POST.get('designation', '').strip()
        updated_organization = request.POST.get('organization', '').strip()
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password', '').strip()

        # Validate fields
        if not updated_name or not updated_designation or not updated_organization:
            messages.error(request, "All fields are required.")
            return redirect('chemist_profile')

        # Verify old password
        if not check_password(old_password, chemist.password):
            messages.error(request, "Old password is incorrect.")
            return redirect('chemist_profile')

        # Update profile fields
        chemist.name = updated_name
        chemist.designation = updated_designation
        chemist.organization = updated_organization

        # Change password if new one is provided
        if new_password:
            chemist.password = make_password(new_password)

        chemist.save()

        # Log out after update (password or not)
        request.session.flush()
        messages.success(request, "Profile updated. Please log in again.")
        return redirect('login')

    return redirect('chemist_profile')


# Other Pages (Render Only)
def add_profile(request):
    return render(request, 'manage/addprofile.html')


@csrf_exempt
def save_profile(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            name = data.get("name")
            kit = data.get("kit")
            date = data.get("date")
            alleles = data.get("alleles")

            # Save the DNAProfile
            profile = DNAProfile.objects.create(
                name=name,
                kit_name=kit,
                date_added=date
            )

            # Save ProfileAlleles
            for item in alleles:
                ProfileAllele.objects.create(
                    profile=profile,
                    locus_name=item["locus"],
                    allele_1=item["allele1"],
                    allele_2=item["allele2"]
                )

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=405)


def get_dna_profiles(request):
    profiles = DNAProfile.objects.all().order_by('-date_added')
    data = []
    for profile in profiles:
        data.append({
            'id': profile.profile_id,
            'name': profile.name,
            'kit': profile.kit_name,
            'date': profile.date_added.strftime('%Y-%m-%d'),
        })
    return JsonResponse({'profiles': data})

def duo_test(request):
    return render(request, 'manage/duo_parentage_test.html')

@csrf_exempt
def run_duo_paternity_test(request):  # ✅ Keep view name same
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        body = json.loads(request.body)
        profile_a_id = body.get("profile_a")
        profile_b_id = body.get("profile_b")

        if not profile_a_id or not profile_b_id:
            return JsonResponse({"error": "Both profiles must be selected."}, status=400)

        profile_a = get_object_or_404(DNAProfile, pk=profile_a_id)
        profile_b = get_object_or_404(DNAProfile, pk=profile_b_id)

        # ✅ CORRECT FUNCTION CALL
        result_text, interpretation = run_duo_analysis([profile_a, profile_b])

        for line in result_text.splitlines():
            if line.startswith("Final CPI (cumulative PI product):"):
                formatted_cpi = line.split(":", 1)[1].strip()
            elif line.startswith("Probability of Paternity:"):
                probability_of_paternity = line.split(":", 1)[1].strip()
        else:
            formatted_cpi = formatted_cpi if 'formatted_cpi' in locals() else "0"
            probability_of_paternity = probability_of_paternity if 'probability_of_paternity' in locals() else "0%"

            return JsonResponse({
                "success": True,
                "cpi": formatted_cpi,
                "probability": probability_of_paternity,
                "interpretation": interpretation,
            })

    except Exception as e:
        return JsonResponse({"error": f"Exception occurred: {str(e)}"}, status=500)
    

def trio_test(request):
    return render(request, 'manage/trio_parentage_test.html')

@csrf_exempt
def run_trio_paternity_test(request): 
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        body = json.loads(request.body)
        profile_a_id = body.get("profile_a")
        profile_b_id = body.get("profile_b")
        profile_c_id = body.get("profile_c")

        if not profile_a_id or not profile_b_id or not profile_c_id:
            return JsonResponse({"error": "Both profiles must be selected."}, status=400)

        profile_a = get_object_or_404(DNAProfile, pk=profile_a_id)
        profile_b = get_object_or_404(DNAProfile, pk=profile_b_id)
        profile_c = get_object_or_404(DNAProfile, pk=profile_c_id)


        # ✅ CORRECT FUNCTION CALL
        result_text, interpretation = run_trio_analysis([profile_a, profile_b,profile_c])

        for line in result_text.splitlines():
            if line.startswith("Final CPI:"):
                formatted_cpi = line.split(":", 1)[1].strip()
            elif line.startswith("Probability of Paternity:"):
                probability_of_paternity = line.split(":", 1)[1].strip()
        else:
            formatted_cpi = formatted_cpi if 'formatted_cpi' in locals() else "0"
            probability_of_paternity = probability_of_paternity if 'probability_of_paternity' in locals() else "0%"

            return JsonResponse({
                "success": True,
                "cpi": formatted_cpi,
                "probability": probability_of_paternity,
                "interpretation": interpretation,
            })

    except Exception as e:
        return JsonResponse({"error": f"Exception occurred: {str(e)}"}, status=500)

def complex_test(request):
    return render(request, 'manage/complex_parentage_test.html')

def kinship_analysis(request):
    return render(request, 'manage/kinship_analysis.html')

def sibship_analysis(request):
    return render(request, 'manage/sibship_analysis.html')

def profile_inclusion(request):
    return render(request, 'manage/profile_inclusion_test.html')

def random_match(request):
    return render(request, 'manage/random_match_test.html')

@csrf_exempt
def run_rmp_test(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        body = json.loads(request.body)
        profile_a_id = body.get("profile_a")
        profile_b_id = body.get("profile_b")

        if not profile_a_id or not profile_b_id:
            return JsonResponse({"error": "Both profiles must be selected."}, status=400)

        profile_a = get_object_or_404(DNAProfile, pk=profile_a_id)
        profile_b = get_object_or_404(DNAProfile, pk=profile_b_id)

        # Use updated rmptest logic
        result_text, interpretation = run_rmp_analysis([profile_a, profile_b])

        # Extract formatted RMP value from result_text (as returned by format_rmp_as_power)
        for line in result_text.splitlines():
            if line.startswith("Final RMP (cumulative product):"):
                formatted_rmp = line.split(":", 1)[1].strip()
                break
        else:
            formatted_rmp = "0"

        return JsonResponse({
            "success": True,
            "rmp": formatted_rmp,
            "interpretation": interpretation
        })

    except Exception as e:
        return JsonResponse({"error": f"Exception occurred: {str(e)}"}, status=500)


def report(request):
    return render(request, 'manage/report.html')
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime
from .models import Test, TestProfile, ProfileAllele

def test_full_report(request, test_id):
    test = get_object_or_404(Test, test_id=test_id)
    chemist = test.chemist
    test_profiles = TestProfile.objects.filter(test=test)

    # Profile and allele mapping for display
    profile_data = []
    for tp in test_profiles:
        alleles = ProfileAllele.objects.filter(profile=tp.profile).order_by('locus_name')
        profile_data.append({
            'id': tp.profile.profile_id,
            'name': tp.profile.name,
            'role': tp.role,
            'alleles': alleles
        })

    context = {
        'test': test,
        'profiles': profile_data,
        'current_time': localtime().strftime("%d %B %Y, %I:%M %p")
    }
    return render(request, 'manage/report.html', context)
