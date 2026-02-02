# The Master of Secrets - Password Generator

A Python-based secure password generator that creates strong 20-character passwords and calculates their cryptographic strength.

## Features

- Uses Python's `secrets` module for cryptographically strong random passwords
- Passwords include uppercase letters, lowercase letters, digits, and special characters
- Computes the Shannon entropy of generated passwords to measure randomness
- Estimates how long it would take to crack the password (assuming 1 billion guesses per second)

## Requirements

- Python 3.9 (minimum)
- NumPy
- SciPy

## Installation

Install the required dependencies:

```bash
pip install master-of-secrets
```

## Usage

Run the script:

```bash
secure-me
```

When prompted, type "Yes" to generate a password or "No" to exit:

```
Greetings, The Master of Secrets is at your service!
Would you like to know a secret? (Yes/No): Yes
```

Example output:

```
Password: K9#mP$2xL@4rT&8vN!1q
Estimated crack time: 3.27e+02 years
```

## How It Works

1. Creates a 20-character password using a combination of ASCII letters, digits, and punctuation marks
2. Analyzes the character distribution in the password to calculate its Shannon entropy
3. Estimates the time required to crack the password based on the entropy, assuming an attacker can make 1 billion guesses per second

## Note

The crack time estimation is based on the character distribution entropy of the specific generated password, not the theoretical password space. For a truly random 20-character password from the full character set, the theoretical entropy would be higher.

## Author

Monish Giani (thelazybastard)


## License

MIT Licence 