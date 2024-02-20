import os
import sys
import json
import datetime
from datetime import datetime, timedelta
#source ~/.bashrc

def parse_tasks(master_directory):
    filepath = os.path.join(master_directory, "tasks.md")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    tasks = []
    for line in lines:
        cleaned_line = line.strip()  # Remove leading and trailing whitespaces
        if cleaned_line.startswith("- "):  # this is a task line
            try:
                desc, _, due_date_status = cleaned_line[2:].partition(" Due: ")
                due_date, _, status = due_date_status.partition(" ")
                tasks.append((desc.strip(), datetime.strptime(due_date, "%d/%m/%y"), status.strip()))
            except ValueError:
                # Silently skip lines with unexpected format
                continue
    return tasks

def parse_meetings(master_directory):
    filepath = os.path.join(master_directory, "meetings.md")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    meetings = []
    for line in lines:
        cleaned_line = line.strip()  # Remove leading and trailing whitespaces
        if cleaned_line.startswith("- "):  # this is a meeting line
            try:
                desc, _, datetime_str = cleaned_line[2:].rpartition(" Scheduled: ")
                time_str, _, date_str = datetime_str.partition(" ")
                meetings.append((desc.strip(), datetime.strptime(date_str + " " + time_str, "%d/%m/%y %H:%M")))
            except ValueError:
                # Silently skip lines with unexpected format
                continue

    return meetings


def display_reminders():
    master_directory = get_master_directory()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    three_days_later = today + timedelta(days=4)
    one_week_later = today + timedelta(weeks=1) + timedelta(days=1)
    
    # Read tasks and meetings from the file
    tasks = parse_tasks(master_directory)
    meetings = parse_meetings(master_directory)
    
    # Filter the tasks and meetings
    tasks_today = [t[0] for t in tasks if t[1].date() == today and t[2] == "not complete"]
    tasks_three_days = [(t[0], t[1].date()) for t in tasks if tomorrow <= t[1].date() < three_days_later and t[2] == "not complete"]
    
    meetings_today = [(m[0], m[1].time()) for m in meetings if m[1].date() == today]
    meetings_week = [(m[0], m[1].date(), m[1].time()) for m in meetings if tomorrow <= m[1].date() < one_week_later]
    
    # Display tasks and meetings
    print("Just a friendly reminder! You have these tasks to finish today.")
    for task in tasks_today:
        print(f"- {task}")

    print("\nThese tasks need to be finished in the next three days!")   
    for task, date in tasks_three_days:
        formatted_date = date.strftime("%d/%m/%y")
        print(f"- {task} by {formatted_date}")

    print("\nYou have the following meetings today!") 
    for meeting, time in meetings_today:
        formatted_time = time.strftime("%H:%M")
        print(f"- {meeting} at {formatted_time}")

    print("\nYou have the following meetings scheduled over the next week!")
    for meeting, date, time in meetings_week:
        formatted_date = date.strftime("%d/%m/%y")
        formatted_time = time.strftime("%H:%M")
        print(f"- {meeting} on {formatted_date} at {formatted_time}")

SETTINGS_PATH = os.path.expanduser("~/.jafr/user-settings.json")

def get_master_directory():
    with open(SETTINGS_PATH, 'r') as f:
        data = json.load(f)
    return data['master']

def update_master_directory(new_path):
    with open(SETTINGS_PATH, 'w') as f:
        json.dump({"master": new_path}, f)

def change_master_directory():
    new_path = input("Which directory would you like Jafr to use?\n").strip()
    if not os.path.exists(new_path):
        try:
            os.makedirs(new_path, exist_ok=True)
            update_master_directory(new_path)
            print(f"Master directory changed to {new_path}.")
        except Exception as e:
            print(f"Error creating or updating the master directory: {e}")
    else:
        if os.path.isdir(new_path):
            update_master_directory(new_path)
            print(f"Master directory changed to {new_path}.")
        else:
            print(f"The provided path, {new_path}, is not a directory.")

def complete_tasks():
    master_directory = get_master_directory()
    tasks = parse_tasks(master_directory)

    # Filter only the not complete tasks
    incomplete_tasks = [task for task in tasks if task[2] == "not complete"]

    if not incomplete_tasks:
        print("No tasks to complete!")
        return

    print("Which task(s) would you like to mark as completed?")
    for idx, (desc, due_date, _) in enumerate(incomplete_tasks, start=1):
        formatted_date = due_date.strftime("%d/%m/%y")
        print(f"{idx}. {desc} by {formatted_date}")

    while True:  # Loop for input

        input_str = input().strip()

        try:
            selected_indexes = list(map(int, input_str.split()))
            if all(1 <= idx <= len(incomplete_tasks) for idx in selected_indexes):
                break  # Exit the loop if all indexes are valid
            else:
                print("Invalid task num. Please enter a valid option.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by spaces.")

    with open(os.path.join(master_directory, "tasks.md"), 'r') as f:
        lines = f.readlines()

    index_map = {}
    task_count = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("- ") and "Due:" in line:
            task_count += 1
            index_map[task_count] = i

    if len(tasks) != task_count:
        print("Error: The tasks.md file and the tasks list are not aligned.")
        return

    for idx in selected_indexes:
        task_to_complete = incomplete_tasks[idx - 1]
        task_line_num = index_map[tasks.index(task_to_complete) + 1]
        lines[task_line_num] = lines[task_line_num].replace("not complete", "complete")

    with open(os.path.join(master_directory, "tasks.md"), 'w') as f:
        f.writelines(lines)

    print("Marked as complete.")
def add_new_meeting():
    # Get meeting description, date, and time from user
    meeting_desc = input("Please enter a meeting description:\n").strip()
    while True:
        if meeting_desc:
            break
        meeting_desc = input("Invalid meeting description. Please try again.\n").strip()
    
    # Get meeting date from user
    meeting_date = input("Please enter a date:\n").strip()
    while True:
        # Check if date is valid
        try:
            datetime.strptime(meeting_date, "%d/%m/%y")
            break
        except ValueError:
            meeting_date = input("Invalid date format. Please use dd/mm/yy.\n").strip()

    # Get meeting time from user
    meeting_time = input("Please enter a time:\n").strip()
    while True:
        # Check if time is valid
        try:
            datetime.strptime(meeting_time, "%H:%M")
            break
        except ValueError:
            meeting_time = input("Invalid time format. Please use HH:MM.\n").strip()
    
    try:
        # Validate date and time format
        datetime_obj = datetime.strptime(meeting_date + " " + meeting_time, "%d/%m/%y %H:%M")
    except ValueError:
        print("Invalid date or time format. Please use dd/mm/yy for date and HH:MM for time.")
        return

    # Append meeting to meetings.md
    filepath = os.path.join(get_master_directory(), "meetings.md")
    with open(filepath, 'a') as f:
        f.write(f"\n##### added by you\n- {meeting_desc} Scheduled: {meeting_time} {meeting_date}\n")
    
    print(f"Ok, I have added {meeting_desc} on {meeting_date} at {meeting_time}.")

    # Check if user wants to share the meeting
    while True:
        share_choice = input("Would you like to share this meeting? [y/n]: ").strip().lower()
        if share_choice in ['y', 'n']:
            break
        print("Invalid choice. Please enter 'y' or 'n'.")

    if share_choice == 'y':
        share_task_or_meeting(task_or_meeting="meeting", recently_added=True)

custom_passwd_file_path = None

if len(sys.argv) > 1:  # Check if a command-line argument exists
    custom_passwd_file_path = sys.argv[1]


def get_passwd_file_path():
    """
    Determine the appropriate passwd file path.
    
    If a custom passwd file path is provided, use it.
    Else if a passwd file exists in the parent directories or current working directory's tree, use it.
    Otherwise, default to /home/passwd.
    """
    if custom_passwd_file_path:  # Check if a custom path is provided
        return custom_passwd_file_path

    # Check parent directories
    current_dir = os.getcwd()
    potential_path = os.path.join(current_dir, 'passwd')
    
    if os.path.exists(potential_path):
        return potential_path
    
    # Default to the home passwd file
    return "/home/passwd"


def get_all_users():
    """
    Returns a dictionary where the key is the user's name and the value is a tuple of their ID and their home directory.
    """
    user_dict = {}
    with open(get_passwd_file_path(), 'r') as f:  # use the new function here
        for line in f.readlines():
            parts = line.strip().split(':')
            username, user_id, home_directory = parts[0], parts[2], parts[5]
            user_dict[username] = (user_id, home_directory)
    return user_dict

def get_user_master_directory(username):
    """
    Return the master directory for a given user.
    """
    _, home_directory = get_all_users().get(username, (None, None))
    if home_directory:
        jafr_directory = os.path.join(home_directory, ".jafr")
        if not os.path.exists(jafr_directory):
            os.mkdir(jafr_directory)
        
        user_settings_path = os.path.join(jafr_directory, "user-settings.json")
        if not os.path.exists(user_settings_path):
            with open(user_settings_path, 'w') as f:
                json.dump({"master": None}, f)
        
        with open(user_settings_path, 'r') as f:
            data = json.load(f)
        return data.get('master', None)
    return None


def share_task_or_meeting(task_or_meeting="task", recently_added=False):
    """Allow users to share a task or a meeting with others."""
    master_directory = get_master_directory()
    
    current_user_name = master_directory.split("/")[-2]
    if not current_user_name:
        current_user_name = "user"

    items = parse_tasks(master_directory) if task_or_meeting == "task" else parse_meetings(master_directory)
    
    # Only prompt for selection if the item was not recently added
    if not recently_added:
        print(f"Which {task_or_meeting} would you like to share?")
        for idx, (desc, date, *_) in enumerate(items, start=1):
            formatted_date = date.strftime("%d/%m/%y")
            if task_or_meeting == "task":
                print(f"{idx}. {desc} by {formatted_date}")
            else:
                formatted_time = date.strftime("%H:%M")
                print(f"{idx}. {desc} on {formatted_date} at {formatted_time}")

        while True:
            try:
                selected_index = int(input())
                if 1 <= selected_index <= len(items):
                    selected_item = items[selected_index - 1]
                    break
                else:
                    print(f"Invalid {task_or_meeting} number. Please enter a valid number.")
            except ValueError:
                print(f"Invalid {task_or_meeting} number. Please enter a valid number.")
    else:
        # If the item was recently added, select the last item
        selected_item = items[-1]

    users = get_all_users()
    print("Who would you like to share with?")
    for user_name, (user_id, _) in users.items():
        if user_name != current_user_name:  # Excluding the current user from the list
            print(f"{user_id} {user_name}")  # Showing user ID with user name for clarity

    while True:
        user_ids_to_share = input().split()
        valid_user_ids = [user_id for user_id in user_ids_to_share if user_id in [value[0] for value in users.values()] and user_id != users[current_user_name][0]]
        if len(valid_user_ids) == len(user_ids_to_share):
            break
        print("Invalid user ID. Please enter a valid user ID or press enter to exit.")

    for user_id in valid_user_ids:
        user_name = next((key for key, value in users.items() if value[0] == user_id), None)
        if not user_name or user_name == current_user_name: # Check if the user name exists and is not the current user
            continue
        
        user_master_directory = get_user_master_directory(user_name)
        
        file_path = os.path.join(user_master_directory, f"{task_or_meeting}s.md")
        if not os.path.exists(file_path):
            with open(file_path, 'w'):  # This will create the file if it doesn't exist
                pass
        
        with open(file_path, 'a') as f:
            desc, *_ = selected_item
            if task_or_meeting == "task":
                formatted_date = selected_item[1].strftime("%d/%m/%y")
                status = selected_item[2]
                f.write(f"\n##### shared by {current_user_name}\n- {desc} Due: {formatted_date} {status}\n")
            else:  # for meeting
                formatted_date = selected_item[1].strftime("%d/%m/%y")
                formatted_time = selected_item[1].strftime("%H:%M")
                f.write(f"\n##### shared by {current_user_name}\n- {desc} Scheduled: {formatted_time} {formatted_date}\n")

    print(f"{task_or_meeting.capitalize()} shared.")

def check_files_exist():
    """
    Check if tasks.md or meetings.md exist in the user's master directory.
    If they don't exist, print an error message and exit.
    """
    master_directory = get_master_directory() #fetch master directory
    
    # Check if the master directory exists
    if not os.path.exists(master_directory):
        sys.stderr.write("Jafr's chosen master directory does not exist.\n")
        sys.exit(1)
    
    # Check for tasks.md and meetings.md
    tasks_path = os.path.join(master_directory, "tasks.md")
    meetings_path = os.path.join(master_directory, "meetings.md")
    
    if not (os.path.exists(tasks_path) and os.path.exists(meetings_path)):
        sys.stderr.write("Missing tasks.md or meetings.md file.\n")
        sys.exit(1)


def menu():
    check_files_exist()
    display_reminders()
    print("")
    while True:
        
        print("What would you like to do?")
        print("1. Complete tasks")
        print("2. Add a new meeting.")
        print("3. Share a task.")
        print("4. Share a meeting.")
        print("5. Change Jafr's master directory.")
        print("6. Exit")
        choice = input("").strip()
        
        if choice == '1':
            complete_tasks()
            
        elif choice == '2':
            add_new_meeting()
            
        elif choice == '3':
            share_task_or_meeting("task")
            
        elif choice == '4':
            share_task_or_meeting("meeting")
            
        elif choice == '5':
            change_master_directory()
            
        elif choice == '6':
            break
        else:
            print("Invalid choice. Please choose a number from 1 to 6.")
            break

if __name__ == '__main__':
    menu()
