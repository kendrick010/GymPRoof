from supabase import create_client

from .routine_commands import CommandPackage, bot_commands
from .config import SupabaseConfig

# Initialize the Supabase client
supabase_config = SupabaseConfig()
supabase_client = create_client(supabase_config.url, supabase_config.api_key)

def add_streak(user_id: str, command_package: CommandPackage):
    data = {
        "user_id": user_id,
        "routine_type": command_package.command_name
    }

    supabase_client.table("streaks").insert(data).execute()

def summarize_streak(user_id: str):
    columns = [f"{routine}_days" for routine in bot_commands.keys()]
    response = supabase_client.table("streak_view").select(*columns).filter('user_id', 'eq', user_id).limit(1).execute()

    summary = response.data[0] if response.data else dict()

    return summary

def punish_user(user_id: str, command_package: CommandPackage):
    punishment_amount = command_package.get_member("punishment")
    query_callable = command_package.get_member("query")
    query = query_callable(user_id)

    # Execute validation query
    response = query.execute()
    complete_status = response.data.values()[0]

    if not complete_status:
        data = {
            "user_balance": f"(user_balance + {punishment_amount})"
        }
        supabase_client.table("users").update(data).filter('user_id', 'eq', user_id).execute()

        return True

    return False

def add_user(user_id: str):
    data = {
        "user_id": user_id
    }

    supabase_client.table('users').upsert(data, on_conflict=["user_id"]).execute()

def get_users():
    response = supabase_client.table('users').select('user_id').execute()
    
    return response.data

def get_balance(user_id: str):
    response = supabase_client.table('users').select('user_balance').filter('user_id', 'eq', user_id).limit(1).execute()

    return response.data[0]

def update_balance(user_id: str, new_balance: float):
    data = {
        "user_balance": new_balance
    }

    supabase_client.table("users").update(data).filter('user_id', 'eq', user_id).execute()

def update_opted_routine(user_id: str, command_package: CommandPackage):
    queried_routines = get_opted_routines(user_id=user_id)

    # Enforce uniqueness
    queried_routines = set(queried_routines)
    queried_routines.add(command_package.command_name)
    queried_routines = list(queried_routines)

    data = {
        "opted_routines": queried_routines
    }

    supabase_client.table("users").update(data).filter('user_id', 'eq', user_id).execute()

def drop_opted_routine(user_id: str, command_package: CommandPackage):
    queried_routines = get_opted_routines(user_id=user_id)

    # Enforce uniqueness
    queried_routines = set(queried_routines)
    queried_routines.discard(command_package.command_name)
    queried_routines = list(queried_routines)

    data = {
        "opted_routines": queried_routines
    }

    supabase_client.table("users").update(data).filter('user_id', 'eq', user_id).execute()

def get_opted_routines(user_id: str):
    response = supabase_client.table("users").select("opted_routines").filter('user_id', 'eq', user_id).limit(1).execute()
    queried_routines = response.data[0]["opted_routines"]

    return queried_routines

def get_opted_users(command_package: CommandPackage):
    routine_type = command_package.command_name
    response = supabase_client.table("users").select("user_id").filter("opted_routines", "@>", f'["{routine_type}"]').execute()
    
    return response.data