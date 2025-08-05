from decimal import Decimal, getcontext
from frontend.utils.allele_frequencies import ALLELE_FREQS
import math

# High precision for decimal calculations
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

def run_trio_analysis(profiles):
    if len(profiles) != 3:
        return "Error: Trio test requires exactly three DNA profiles (Father, Mother, Child).", ""

    father, mother, child = profiles
    if father.kit_name != mother.kit_name or mother.kit_name != child.kit_name:
        return "Error: All profiles must use the same STR kit.", ""

    kit_name = father.kit_name
    father_alleles = {a.locus_name: sorted([a.allele_1, a.allele_2]) for a in father.alleles.all()}
    mother_alleles = {a.locus_name: sorted([a.allele_1, a.allele_2]) for a in mother.alleles.all()}
    child_alleles = {a.locus_name: sorted([a.allele_1, a.allele_2]) for a in child.alleles.all()}

    loci_to_check = sorted(child_alleles.keys())
    result_lines = [f"STR Kit Used: {kit_name}", "=" * 50]
    cpi_product = Decimal(1)
    matched_loci_count, total_loci = 0, 0
    maternal_mismatch_found = False

    for locus in loci_to_check:
        total_loci += 1
        result_lines.append(f"\nLocus: {locus}")
        print(f"\nProcessing locus: {locus}")

        if locus not in father_alleles or locus not in mother_alleles:
            result_lines.append(f"{locus}: Missing in one of the parent profiles → Skipped.")
            continue

        child_vals = sorted([str(a).strip() for a in child_alleles[locus]])
        mother_vals = sorted([str(a).strip() for a in mother_alleles[locus]])
        father_vals = sorted([str(a).strip() for a in father_alleles[locus]])

        print(f"Child: {child_vals}, Mother: {mother_vals}, Father: {father_vals}")

        maternal_contrib = []
        paternal_contrib = []

        if child_vals == mother_vals:
            # Special case: child and mother identical — assign to father first
            possible_paternal = set(father_vals).intersection(child_vals)
            if possible_paternal:
                paternal_allele = sorted(possible_paternal)[0]
                maternal_contrib = [a for a in child_vals if a != paternal_allele]
                if not maternal_contrib and len(child_vals) == 2:
                    maternal_contrib = [child_vals[1]]  # fallback
                print(f"Special Case: maternal=child → Assigning {paternal_allele} to father, {maternal_contrib} to mother")
            else:
                result_lines.append(f"{locus}: Father does not share allele with child → PI = 0.")
                print(f"{locus}: Father excluded due to no matching allele. CPI = 0")
                cpi_product = Decimal(0)
                continue
        else:
            # Normal case: assign one allele to mother
            temp_child = child_vals.copy()
            temp_mother = mother_vals.copy()
            for allele in child_vals:
                if allele in temp_mother:
                    maternal_contrib = [allele]
                    temp_mother.remove(allele)
                    temp_child.remove(allele)
                    break

            if not maternal_contrib:
                result_lines.append(f"{locus}: No maternal allele matched → Test invalid.")
                print(f"{locus}: Error – no maternal match. Aborting.")
                maternal_mismatch_found = True
                break

            if not temp_child:
                result_lines.append(f"{locus}: No paternal allele remains after maternal assignment → PI = 0.")
                print(f"{locus}: No paternal allele found. CPI = 0")
                cpi_product = Decimal(0)
                continue

            paternal_allele = temp_child[0]

        # Validate paternal match
        if paternal_allele not in father_vals:
            result_lines.append(f"{locus}: Alleged father does not carry allele '{paternal_allele}' → PI = 0.")
            print(f"{locus}: Father missing allele. CPI = 0")
            cpi_product = Decimal(0)
            continue

        matched_loci_count += 1
        p = get_allele_frequency_for_locus(kit_name, locus, paternal_allele)
        if p is None:
            result_lines.append(f"{locus}: Allele frequency not found for {paternal_allele} → Skipped.")
            print(f"{locus}: Missing frequency, skipped.")
            continue

        if child_vals[0] == child_vals[1]:
            pi = Decimal(1) / Decimal(p)
            print(f"{locus}: Homozygous child → PI = 1 / {p} = {pi}")
        else:
            pi = Decimal(0.5) / Decimal(p)
            print(f"{locus}: Heterozygous child → PI = 0.5 / {p} = {pi}")

        result_lines.append(f"{locus}: PI = {pi:.10E} (Paternal allele: {paternal_allele})")
        cpi_product *= pi
        print(f"{locus}: Cumulative CPI = {cpi_product}")

    if maternal_mismatch_found:
        return "Error: Mother profile does not match the child's DNA at one or more loci.\nPlease ensure the correct mother profile is used.", "Invalid mother profile."

    if matched_loci_count == 0:
        return "No informative loci available. Cannot compute CPI.", "Alleged father is excluded."

    prob_of_paternity = float(cpi_product) / (float(cpi_product) + 1)
    prob_percentage = prob_of_paternity * 100
    interpretation = interpret_paternity_probability(prob_percentage)
    formatted_cpi = format_cpi_as_power(cpi_product)

    result_lines.append("\n" + "=" * 50)
    result_lines.append(f"Matched Loci: {matched_loci_count} / {total_loci}")
    result_lines.append(f"Final CPI: {formatted_cpi}")
    result_lines.append(f"Probability of Paternity: {prob_percentage:.2f}%")
    result_lines.append(f"Interpretation: {interpretation}")

    print("\n========== Final Summary ==========")
    print(f"Matched Loci: {matched_loci_count}/{total_loci}")
    print(f"Final CPI: {formatted_cpi}")
    print(f"Probability of Paternity: {prob_percentage:.2f}%")
    print(f"Interpretation: {interpretation}")

    return "\n".join(result_lines), interpretation
