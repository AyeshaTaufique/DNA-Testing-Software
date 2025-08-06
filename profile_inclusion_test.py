from decimal import Decimal, getcontext
from frontend.utils.allele_frequencies import ALLELE_FREQS
import math
from collections import defaultdict

# Set high precision for decimal calculations
getcontext().prec = 30

def get_allele_frequency_for_locus(kit_name, locus, allele):
    try:
        return Decimal(str(ALLELE_FREQS[kit_name][locus][str(allele)]))
    except KeyError:
        return None
def interpret_cpi(cumulative_cpi):
    if cumulative_cpi < 0.000001:
        return "The profile is very specific; almost no one in the population would match by chance."
    elif 0.000001 <= cumulative_cpi < 0.001:
        return "Only a very small group of people could match this profile."
    elif 0.001 <= cumulative_cpi < 0.01:
        return "The profile is rare; few people in the population could match."
    elif 0.01 <= cumulative_cpi < 0.1:
        return "The profile is moderately rare; a moderate portion of the population could be included."
    elif 0.1 <= cumulative_cpi < 1:
        return "Weak evidence of inclusion; a notable portion of the population could be included."
    else:
        return "Very weak or no evidence of inclusion; the profiles do not effectively discriminate within the population."

def format_cpi_as_power(cpi_decimal):
    if cpi_decimal == 0:
        return "0"
    exponent = math.floor(math.log10(float(cpi_decimal)))
    base = float(cpi_decimal) / (10 ** exponent)
    return f"{base:.2f} × 10^{exponent}"

def profile_inclusion_analysis(profiles):
    if len(profiles) < 2:
        return "Error: At least two DNA profiles are required for Profile Inclusion Test.", ""

    kit_name = profiles[0].kit_name
    for profile in profiles:
        if profile.kit_name != kit_name:
            return "Error: All profiles must use the same STR kit.", ""

    # Gather alleles by locus
    locus_allele_pool = defaultdict(list)
    for idx, profile in enumerate(profiles, start=1):
        print(f"\nProfile {idx} (ID: {profile.profile_id}) Alleles:")
        for allele_obj in profile.alleles.all():
            locus = allele_obj.locus_name
            allele1 = allele_obj.allele_1
            allele2 = allele_obj.allele_2
            locus_allele_pool[locus].append(allele1)
            locus_allele_pool[locus].append(allele2)
            print(f"  Locus {locus}: Allele 1 = {allele1}, Allele 2 = {allele2}")

    result_lines = [f"STR Kit Used: {kit_name}", f"{'=' * 50}\n"]
    cumulative_cpi = Decimal(1.0)
    total_loci = 0

    result_lines.append(f"Locus: {locus}")

    for locus, alleles in locus_allele_pool.items():
        total_loci += 1
        print(f"\nProcessing locus: {locus}")
        print(f"  All alleles across profiles: {alleles}")

        freq_sum = Decimal(0)
        unique_alleles = set(alleles)

        result_lines.append(f"Locus: {locus}")

        for allele in unique_alleles:
            freq = get_allele_frequency_for_locus(kit_name, locus, allele)
            if freq is None:
                result_lines.append(f"  Allele {allele}: Frequency not found. Skipped.")
                print(f"  Allele {allele}: Frequency not found. Skipped.")
                continue
            freq_sum += freq
            result_lines.append(f"  Allele {allele}: freq = {freq}")
            print(f"    Allele {allele}: freq = {freq}")

        print(f"  ➕ Sum of unique allele frequencies at {locus}: {freq_sum}")
        pi_value = freq_sum ** 2
        print(f"  🔁 PI (squared sum) at {locus}: {pi_value}")
        cumulative_cpi *= pi_value
        print(f"  📊 Updated cumulative CPI after {locus}: {cumulative_cpi}")

        result_lines.append(f"  Sum of allele frequencies: {freq_sum}")
        result_lines.append(f"  PI for {locus}: {pi_value:.15E}")
        result_lines.append("-")


    cpi_percentage = float(cumulative_cpi) * 100
    interpretation = interpret_cpi(cpi_percentage)
    formatted_cpi = format_cpi_as_power(cumulative_cpi)

    result_lines.append(f"\n{'=' * 50}")
    result_lines.append(f"Total Loci Processed: {total_loci}")
    result_lines.append(f"Final CPI (cumulative product): {formatted_cpi}")
    result_lines.append(f"Final CPI as percentage: {cpi_percentage:.30f}%")
    result_lines.append(f"Interpretation:\n{interpretation}")

    print(f"\nFinal CPI: {formatted_cpi}")
    print(f"Final CPI percentage: {cpi_percentage:.30f}%")
    print(f"Interpretation: {interpretation}")

    return "\n".join(result_lines), interpretation
