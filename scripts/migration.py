import json

def migrate_personality_trait():
    """
    Migrates the `preferred_atmosphere` field to `personality_trait` for all users.
    "외향" -> "외향"
    "내향" -> "내향"
    "밸런스" -> "중간"
    """
    with open('data/users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    for user in users:
        if 'preferred_atmosphere' in user:
            if user['preferred_atmosphere'] == '밸런스':
                user['personality_trait'] = '중간'
            else:
                user['personality_trait'] = user['preferred_atmosphere']
            del user['preferred_atmosphere']

    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    migrate_personality_trait()
    print("Migration complete. 'preferred_atmosphere' has been migrated to 'personality_trait'.")