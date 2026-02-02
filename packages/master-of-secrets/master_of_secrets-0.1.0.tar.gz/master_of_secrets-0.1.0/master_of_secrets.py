import secrets
import string
import numpy as np
from scipy.stats import entropy


def main():
    display_strength()

def get_user_input():
    print("Greetings, The Master of Secrets is at your service!")

    user_input = input("Would you like to know a secret? (Yes/No): ")

    return user_input

def generate_password():
    user_input = get_user_input()

    if user_input == "Yes":
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for _ in range(20))
        return password
    elif user_input == "No":
        print ("Come back soon!")

    return None


def calculate_entropy(password):
    chars, counts = np.unique(list(password), return_counts=True)
    probabilities = counts / len(password)
    ent = entropy(probabilities, base=2)

    return ent


def crack_time(entropy_bits, guesses_per_second=1e9):
    total_combinations = 2 ** entropy_bits

    avg_seconds = total_combinations / (2 * guesses_per_second)
    seconds_per_year = 365.25 * 24 * 60 * 60
    years = avg_seconds / seconds_per_year

    return years


def display_strength():
    password = generate_password()

    if password is None:
        return

    ent = calculate_entropy(password)
    year = crack_time(ent)


    print(f"Password: {password}")
    print(f"Estimated crack time: {year:.2e} years")

