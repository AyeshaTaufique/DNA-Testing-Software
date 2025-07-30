from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class ChemistManager(BaseUserManager):
    def create_user(self, email, name, designation, organization, password=None):
        if not email:
            raise ValueError("Chemists must have an email address")
        chemist = self.model(
            email=self.normalize_email(email),
            name=name,
            designation=designation,
            organization=organization,
        )
        chemist.set_password(password)
        chemist.save(using=self._db)
        return chemist

class Chemist(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    designation = models.CharField(max_length=100)
    organization = models.CharField(max_length=100)
    password = models.CharField(max_length=128)  # Hashed password

    def __str__(self):
        return self.name

# Profile info

class DNAProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    kit_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.kit_name})"


class ProfileAllele(models.Model):
    profile = models.ForeignKey(DNAProfile, on_delete=models.CASCADE, related_name='alleles')
    locus_name = models.CharField(max_length=50)
    allele_1 = models.CharField(max_length=10)
    allele_2 = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.locus_name}: {self.allele_1}, {self.allele_2}"

class Test(models.Model):
    TEST_TYPE_CHOICES = [
        ('random_match', 'Random Match'),
        ('profile_inclusion', 'Profile Inclusion'),
        ('duo_parentage', 'Duo Parentage'),
        ('trio_parentage', 'Trio Parentage'),
        ('sibship_analysis','Sibship Analysis'),
        ('kinship', 'Kinship'),
        ('complex', 'Complex Parentage'),
        # Add more as needed
    ]

    test_id = models.AutoField(primary_key=True)
    chemist = models.ForeignKey(Chemist, on_delete=models.CASCADE, related_name='tests')
    test_type = models.CharField(max_length=50, choices=TEST_TYPE_CHOICES)
    date_run = models.DateTimeField(auto_now_add=True)
    test_result = models.TextField(blank=True, null=True)
    result_interpretation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Test {self.test_id} by {self.chemist.name}"

class TestProfile(models.Model):
    ROLE_CHOICES = [
        ('Individual', 'Individual'),         # For RMP, Identity
        ('Mother', 'Mother'),
        ('Father', 'Father'),
        ('Alleged Father', 'Alleged Father'),
        ('Child', 'Child'),
        ('Sibling', 'Sibling'),
        ('Grandparent', 'Grandparent'),
        ('Uncle/Aunt', 'Uncle/Aunt'),
        ('Cousin', 'Cousin'),
        ('Reference', 'Reference'),           # For Identity/Inclusion
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    profile = models.ForeignKey('DNAProfile', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"TestProfile {self.profile.id} in Test #{self.test.id} as {self.role or 'Unassigned'}"
