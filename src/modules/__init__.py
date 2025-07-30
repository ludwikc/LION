this_package = 'modules'

active = [
    '.sysadmin',
    '.config',
    '.user_config',
    '.skins',
    '.schedule',
    '.economy',
    '.ranks',
    '.reminders',
    '.shop',
    '.statistics',
    '.pomodoro',
    '.rooms',
    '.tasklist',
    '.rolemenus',
    '.member_admin',
    '.moderation',
    '.video_channels',
    '.meta',
    '.sponsors',
    '.topgg',
    # '.premium',  # Temporarily disabled due to webhook config issue
    '.reactions',
    '.secrets',
    '.test',
]


async def setup(bot):
    for ext in active:
        await bot.load_extension(ext, package=this_package)
