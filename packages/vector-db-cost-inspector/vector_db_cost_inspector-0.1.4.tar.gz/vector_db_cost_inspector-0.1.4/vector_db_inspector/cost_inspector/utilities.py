import sys

def print_header(text):
    print(f"\n\033[1m{text}\033[0m")
    print("=" * 60)

def print_warning(text):
    print(f"\033[93m[!] {text}\033[0m")

def print_success(text):
    print(f"\033[92m[+] {text}\033[0m")

def print_money(text):
    print(f"\033[92m\033[1m$$$ {text} $$$\033[0m")

def get_user_input(prompt, default=None):
    if default:
        user_in = input(f"{prompt} [{default}]: ")
        return user_in.strip() if user_in.strip() else default
    return input(f"{prompt}: ").strip()

def print_cta(savings_found=False):
    """
    Prints a professional footer with contact options.
    Adjusts the tone based on whether savings were found.
    """
    print("\n" + "="*60)
    
    if savings_found:
        print("\033[1m\033[92mWOW! You have significant potential savings.\033[0m")
        print("I am building a specialized tool to automate this cleanup process")
        print("so you don't have to write these scripts yourself.")
        print("\nIf you want early access (or just want me to double-check these numbers):")
    else:
        print("\033[1mThanks for using the Vector Cost Auditor.\033[0m")
        print("I'm an ex-AWS S3 engineer building tools for AI infrastructure.")
        print("If you have feature requests or bugs:")

    # The "Business Card"
    print("-" * 60)
    print("  \033[1mPeihao Chen\033[0m (Creator)")
    print("  \U0001F4E8 \033[4mbillychenph@gmail.com\033[0m")  # Replace with your email
    print("  \U0001F517 \033[4mhttps://www.linkedin.com/in/peihaochen\033[0m") # Replace with your real LinkedIn
    print("  \U0001F418 \033[4mhttps://github.com/billycph/VectorDBCostSavingInspector\033[0m")
    print("-" * 60)
    
    # The "Book a Meeting" Link (The most aggressive conversion tool)
    if savings_found:
        print("  \U0001F4C5 \033[1mBook a 15-min Infra Audit (Free):\033[0m")
        print("  >> \033[4mhttps://calendly.com/billychenph/033[0m <<")
    
    print("="*60 + "\n")
