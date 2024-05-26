print("Loading env variables...")
import datetime
import random
from dotenv import load_dotenv
import argparse
import os

load_dotenv()  # load env variables before importing from app
os.environ["DEV_HOSTNAME"] = "localhost"

from app.models.models import Runs, Users

from app import create_app

flask_config = None
app = None

lorem: str = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
)


def init_env(env: str):
    global flask_config
    global app
    flask_config = env

    print(f"Initializing environment on {env}...")
    app = create_app(env)


def generate_random_time():
    return datetime.time(
        hour=random.randint(7, 19),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )


def generate_runs(for_user: int, num_runs: int = 100):
    print(f"Generating {num_runs} runs for user {for_user} on {flask_config}...")

    with app.app_context():
        user: Users = Users.find(for_user)
        if not user:
            print(f"User {for_user} not found")
            return

        today = datetime.date.today()

        for _ in range(num_runs):
            print(f"Generating run #{_} for user {for_user} on {flask_config}...")

            distance_mi = random.uniform(1, 5)
            runtime_s = distance_mi * (60 * random.randint(7, 9)) + random.randint(
                0, 60
            )

            run: Runs = Runs(
                user_id=for_user,
                date=today - datetime.timedelta(days=random.randint(0, 60)),
                run_start_time=(
                    None if random.random() < 0.3 else generate_random_time()
                ),
                distance_mi=distance_mi,
                runtime_s=runtime_s,
                notes=(
                    ""
                    if random.random() < 0.3
                    else lorem[: random.randint(10, len(lorem))]
                ),
            )

            print(f"Saving run #{_} for user {for_user} on {flask_config}...")
            run.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate runs for a user.")

    parser.add_argument("for_user", type=int, help="User ID for whom to generate runs")
    parser.add_argument(
        "--num_runs",
        type=int,
        default=100,
        help="Number of runs to generate (default: 100)",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        help="Which environment to use (default: dev)",
    )

    args = parser.parse_args()

    init_env(args.env)
    generate_runs(args.for_user, args.num_runs)
