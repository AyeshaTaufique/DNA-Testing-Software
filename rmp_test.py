from decimal import Decimal, getcontext
from frontend.utils.allele_frequencies import ALLELE_FREQS
import math

# Set high precision for decimal calculations
getcontext().prec = 30

def get_allele_frequency_for_locus(kit_name, locus, allele):
    try:
        return ALLELE_FREQS[kit_name][locus][str(allele)]
    except KeyError:
        return None

def interpret_rmp(rmp_percentage):
    if rmp_percentage > 1:
        return "Very weak evidence of common origin."
    elif  0.1 < rmp_percentage <= 1:
        return "Weak to moderate evidence of common origin."
    elif 0.01 < rmp_percentage <= 0.1:
        return "Moderate to strong evidence of common origin"
    elif 0.0001 < rmp_percentage <= 0.01:
        return "Extremely strong evidence of common origin."
    elif rmp_percentage <= 0.0001:
        return "Very strong evidence of common origin."

def format_rmp_as_power(rmp_decimal):
    if rmp_decimal == 0:
        return "0"
    exponent = math.floor(math.log10(float(rmp_decimal)))
    base = float(rmp_decimal) / (10 ** exponent)
    return f"{base:.2f} × 10^{exponent}"

def run_rmp_analysis(profiles):
    if len(profiles) != 2:
        return "Error: RMP Test requires exactly two DNA profiles.", ""

    profile1, profile2 = profiles
    if profile1.kit_name != profile2.kit_name:
        return "Error: Both profiles must use the same STR kit.", ""

    kit_name = profile1.kit_name
    alleles1 = profile1.alleles.all()
    alleles2 = profile2.alleles.all()

    profile1_alleles = {a.locus_name: [a.allele_1, a.allele_2] for a in alleles1}
    profile2_alleles = {a.locus_name: [a.allele_1, a.allele_2] for a in alleles2}

    rmp_product = Decimal(1.0)
    result_lines = [f"STR Kit Used: {kit_name}", f"{'=' * 50}\n"]
    matched_loci_count, total_loci = 0, 0

    for locus in profile1_alleles:
        total_loci += 1
        if locus not in profile2_alleles:
            result_lines.append(f"{locus}: Not found in both profiles → Skipped")
            continue

        alleles_p1 = sorted(profile1_alleles[locus])
        alleles_p2 = sorted(profile2_alleles[locus])

        if alleles_p1 != alleles_p2:
            result_lines.append(f"{locus}: No allele match between profiles → Profiles likely from different individuals.")
            result_lines.append(f"\n{'=' * 50}")
            result_lines.append("RMP calculation aborted due to allele mismatch.")
            interpretation = "Strong evidence that profiles belong to different individuals."
            result_lines.append(f"Interpretation:\n{interpretation}")
            print("Mismatch at locus:", locus)
            return "\n".join(result_lines), interpretation

        matched_loci_count += 1
        a1, a2 = str(alleles_p1[0]).strip(), str(alleles_p1[1]).strip()

        if a1 == a2:
            p = get_allele_frequency_for_locus(kit_name, locus, a1)
            if p is None:
                result_lines.append(f"{locus}: Homozygous match → allele '{a1}' frequency not found.")
                continue
            rmp = Decimal(p) ** 2
            result_lines.append(f"{locus}: Homozygous ({a1}, {a2}) → p² = {p}² = {rmp:.15E}")
            print(f"{locus} (Homozygous): {p}² = {rmp}")
        else:
            p = get_allele_frequency_for_locus(kit_name, locus, a1)
            q = get_allele_frequency_for_locus(kit_name, locus, a2)
            if p is None or q is None:
                result_lines.append(f"{locus}: Heterozygous match → allele frequencies for '{a1}' or '{a2}' not found.")
                continue
            rmp = Decimal(2) * Decimal(p) * Decimal(q)
            result_lines.append(f"{locus}: Heterozygous ({a1}, {a2}) → 2pq = 2*{p}*{q} = {rmp:.15E}")
            print(f"{locus} (Heterozygous): 2*{p}*{q} = {rmp}")

        rmp_product *= rmp
        print(f"Cumulative RMP after {locus}: {rmp_product}")

    if matched_loci_count == 0:
        return (
            "No matching alleles found at any locus. RMP cannot be calculated.",
            "Extremely strong evidence that profiles are from different individuals."
        )

    rmp_percentage = float(rmp_product) * 100
    interpretation = interpret_rmp(rmp_percentage)
    formatted_rmp_power = format_rmp_as_power(rmp_product)

    result_lines.append(f"\n{'=' * 50}")
    result_lines.append(f"Matched Loci: {matched_loci_count} / {total_loci}")
    result_lines.append(f"Final RMP (cumulative product): {formatted_rmp_power}")
    result_lines.append(f"Final RMP as percentage: {rmp_percentage:.15f}%")
    result_lines.append(f"Interpretation:\n{interpretation}")

    print(f"Final RMP: {formatted_rmp_power}, Percentage: {rmp_percentage:.15f}%, Interpretation: {interpretation}")

    return "\n".join(result_lines), interpretation
