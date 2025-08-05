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

def interpret_paternity_probability(prob_percentage):
    if prob_percentage == 0:
        return "Alleged father is 100% excluded as the biological parent."
    elif prob_percentage < 99:
        return "Weak or inconclusive support for paternity."
    elif 99 <= prob_percentage < 99.9:
        return "Moderate to strong support for paternity."
    else:
        return "Very strong support that the alleged father is the biological parent."

def format_cpi_as_power(cpi_decimal):
    if cpi_decimal == 0:
        return "0"
    exponent = math.floor(math.log10(float(cpi_decimal)))
    base = float(cpi_decimal) / (10 ** exponent)
    return f"{base:.2f} × 10^{exponent}"

def run_duo_analysis(profiles):
    print("Starting Duo Paternity Analysis...")
    
    if len(profiles) != 2:
        print("Error: Expected 2 profiles (father and child), received:", len(profiles))
        return "Error: Paternity Test requires exactly two DNA profiles (Alleged Father and Child).", ""

    father, child = profiles
    print(f"Profiles received → Father: {father.name}, Child: {child.name}")

    if father.kit_name != child.kit_name:
        print("STR kit mismatch detected.")
        return "Error: Both profiles must use the same STR kit.", ""

    kit_name = father.kit_name
    print(f"Using STR kit: {kit_name}")

    father_alleles = {a.locus_name: [a.allele_1, a.allele_2] for a in father.alleles.all()}
    child_alleles = {a.locus_name: [a.allele_1, a.allele_2] for a in child.alleles.all()}

    cpi_product = Decimal(1.0)
    result_lines = [f"STR Kit Used: {kit_name}", f"{'=' * 50}\n"]
    matched_loci_count, total_loci = 0, 0

    for locus in child_alleles:
        total_loci += 1
        print(f"\nAnalyzing locus: {locus}")
        
        if locus not in father_alleles:
            print(f"{locus} not found in father's profile. Skipping.")
            result_lines.append(f"{locus}: Not found in both profiles → Skipped")
            continue

        child_vals = [str(a).strip() for a in child_alleles[locus]]
        father_vals = [str(a).strip() for a in father_alleles[locus]]
        print(f"Child alleles: {child_vals}, Father alleles: {father_vals}")

        matched = set(child_vals).intersection(father_vals)
        print(f"Matched alleles: {matched}")

        if not matched:
            print(f"No matching allele at {locus}. Exclusion declared.")
            result_lines.append(f"{locus}: No matching allele between father and child → Alleged father excluded.")
            result_lines.append(f"\n{'=' * 50}")
            result_lines.append("CPI calculation aborted due to allele mismatch.")
            interpretation = "Alleged father is 100% excluded as the biological parent."
            result_lines.append(f"Interpretation:\n{interpretation}")
            return "\n".join(result_lines), interpretation

        matched_loci_count += 1
        matched_allele = list(matched)[0]
        print(f"Using matched allele for PI calculation: {matched_allele}")

        p = get_allele_frequency_for_locus(kit_name, locus, matched_allele)
        print(f"Allele frequency for {matched_allele}: {p}")

        if p is None:
            print(f"Frequency not found for matched allele {matched_allele}. Skipping locus.")
            result_lines.append(f"{locus}: Matched allele '{matched_allele}' frequency not found.")
            continue

        pi = Decimal(1) / Decimal(p)
        print(f"PI at {locus}: 1 / {p} = {pi}")
        result_lines.append(f"{locus}: Matched allele ({matched_allele}) → PI = 1 / {p} = {pi:.15E}")

        cpi_product *= pi
        print(f"Cumulative CPI after {locus}: {cpi_product}")

    if matched_loci_count == 0:
        print("No loci matched. Exclusion assumed.")
        return (
            "No matched alleles at any locus. CPI cannot be calculated.",
            "Alleged father is excluded as biological parent."
        )

    prob_of_paternity = float(cpi_product) / (float(cpi_product) + 1)
    prob_percentage = prob_of_paternity * 100
    interpretation = interpret_paternity_probability(prob_percentage)
    formatted_cpi = format_cpi_as_power(cpi_product)

    print("\n==== Final Result Summary ====")
    print(f"Matched Loci: {matched_loci_count} / {total_loci}")
    print(f"Final CPI: {formatted_cpi}")
    print(f"Probability of Paternity: {prob_percentage:.2f}%")
    print(f"Interpretation: {interpretation}")

    result_lines.append(f"\n{'=' * 50}")
    result_lines.append(f"Matched Loci: {matched_loci_count} / {total_loci}")
    result_lines.append(f"Final CPI (cumulative PI product): {formatted_cpi}")
    result_lines.append(f"Probability of Paternity: {prob_percentage:.2f}%")
    result_lines.append(f"Interpretation:\n{interpretation}")

    return "\n".join(result_lines), interpretation
