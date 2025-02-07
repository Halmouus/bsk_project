
def number_to_french_words(number):
    units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
    teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
    
    def process_hundreds(n):
        if n == 0:
            return ""
        elif n == 1:
            return "cent "
        else:
            return units[n] + " cent "

    def process_below_100(n):
        if n < 10:
            return units[n]
        elif n < 20:
            return teens[n-10]
        elif n % 10 == 0:
            return tens[n//10]
        elif n < 70:
            return tens[n//10] + "-" + units[n%10]
        elif n < 80:
            return "soixante" + ("-" + teens[n-70] if n > 70 else "")
        elif n < 90:
            return "quatre-vingt" + ("-" + units[n-80] if n > 80 else "")
        else:
            return "quatre-vingt" + ("-" + teens[n-90] if n > 90 else "")

    def process_thousands(n):
        if n == 0:
            return ""
        elif n == 1:
            return "mille "
        else:
            return process_below_100(n) + " mille "

    def convert_to_words(n):
        if n == 0:
            return "zéro"
        
        words = ""
        
        # Process millions
        millions = n // 1000000
        if millions > 0:
            if millions == 1:
                words += "un million "
            else:
                words += process_below_100(millions) + " millions "
            n = n % 1000000
        
        # Process thousands
        thousands = n // 1000
        if thousands > 0:
            words += process_thousands(thousands)
            n = n % 1000
        
        # Process hundreds
        hundreds = n // 100
        if hundreds > 0:
            words += process_hundreds(hundreds)
            n = n % 100
        
        # Process rest
        if n > 0:
            if words != "":
                words += "et " if n == 1 else ""
            words += process_below_100(n)
        
        return words.strip()

    try:
        # Split number into dirham and centimes
        dirham = int(number)
        centimes = int(round((number - dirham) * 100))
        
        # Convert dirham
        dirham_text = convert_to_words(dirham)
        
        # Build final text
        text = dirham_text + " dirham"
        if dirham > 1:  # Add 's' for plural
            text += "s"
            
        # Add centimes if any
        if centimes > 0:
            centimes_text = convert_to_words(centimes)
            text += " et " + centimes_text + " centime"
            if centimes > 1:  # Add 's' for plural
                text += "s"
        
        return text.upper()  # Convert to uppercase for checks
        
    except Exception as e:
        print(f"Error converting number to words: {e}")
        return ""

def amount_to_french_words(value):
    """Template filter for converting numbers to French words"""
    try:
        return number_to_french_words(float(value))
    except (ValueError, TypeError):
        return ""