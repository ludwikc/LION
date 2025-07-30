import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands as cmds
from discord import app_commands as appcmds
from discord.ui.button import ButtonStyle

from meta import LionBot, LionCog, LionContext
from core.lion_guild import VoiceMode
from utils.lib import error_embed
from utils.ui import LeoUI, AButton, utc_now
from gui.base import CardMode
from wards import high_management_ward

from . import babel
from .data import StatsData
from .ui import ProfileUI, WeeklyMonthlyUI, LeaderboardUI
from .settings import StatisticsSettings, StatisticsConfigUI
from .graphics.profilestats import get_full_profile
from .achievements import get_achievements_for

_p = babel._p


logger = logging.getLogger(__name__)


class StatsCog(LionCog):
    def __init__(self, bot: LionBot):
        self.bot = bot
        self.data = bot.db.load_registry(StatsData())
        self.settings = StatisticsSettings()

    async def cog_load(self):
        await self.data.init()

        self.bot.core.user_config.register_model_setting(self.settings.UserGlobalStats)
        self.bot.core.guild_config.register_model_setting(self.settings.SeasonStart)
        self.bot.core.guild_config.register_setting(self.settings.UnrankedRoles)

        configcog = self.bot.get_cog('ConfigCog')
        self.crossload_group(self.configure_group, configcog.admin_config_group)

    @cmds.hybrid_command(
        name=_p('cmd:me', "me"),
        description=_p(
            'cmd:me|desc',
            "Edit your personal profile and see your statistics."
        )
    )
    @appcmds.guild_only
    async def me_cmd(self, ctx: LionContext):
        await ctx.interaction.response.defer(thinking=True)
        ui = ProfileUI(self.bot, ctx.author, ctx.guild)
        await ui.run(ctx.interaction)
        await ui.wait()

    @cmds.hybrid_command(
        name=_p('cmd:profile', 'profile'),
        description=_p(
            'cmd:profile|desc',
            "Display the target's profile and statistics summary."
        )
    )
    @appcmds.rename(
        member=_p('cmd:profile|param:member', "member")
    )
    @appcmds.describe(
        member=_p(
            'cmd:profile|param:member|desc', "Member to display profile for."
        )
    )
    @appcmds.guild_only
    async def profile_cmd(self, ctx: LionContext, member: Optional[discord.Member] = None):
        if not ctx.guild:
            return
        if not ctx.interaction:
            return

        member = member if member is not None else ctx.author
        if member.bot:
            # TODO: Localise
            await ctx.reply(
                "Bots cannot have profiles!",
                ephemeral=True
            )
            return
        await ctx.interaction.response.defer(thinking=True)
        # Ensure the lion exists
        await self.bot.core.lions.fetch_member(member.guild.id, member.id, member=member)

        if ctx.lguild.guild_mode.voice:
            mode = CardMode.VOICE
        else:
            mode = CardMode.TEXT

        profile_data = await get_full_profile(self.bot, member.id, member.guild.id, mode)
        with profile_data:
            file = discord.File(profile_data, 'profile.png')
            await ctx.reply(file=file)


    @cmds.hybrid_command(
        name=_p('cmd:stats', "stats"),
        description=_p(
            'cmd:stats|desc',
            "Weekly and monthly statistics for your recent activity."
        )
    )
    @appcmds.guild_only
    async def stats_cmd(self, ctx: LionContext):
        """
        Statistics command.
        """
        await ctx.interaction.response.defer(thinking=True)
        ui = WeeklyMonthlyUI(self.bot, ctx.author, ctx.guild)
        await ui.run(ctx.interaction)


        await ui.wait()

    @cmds.hybrid_command(
        name=_p('cmd:leaderboard', "leaderboard"),
        description=_p(
            'cmd:leaderboard|desc',
            "Server leaderboard."
        )
    )
    @appcmds.guild_only
    async def leaderboard_cmd(self, ctx: LionContext):
        if not ctx.guild:
            return
        if not ctx.interaction:
            return
        if not ctx.guild.chunked:
            t = self.bot.translator.t
            waiting_embed = discord.Embed(
                colour=discord.Colour.greyple(),
                description=t(_p(
                    'cmd:leaderboard|chunking|desc',
                    "Requesting server member list from Discord, please wait {loading}"
                )).format(loading=self.bot.config.emojis.loading),
                timestamp=utc_now(),
            )
            await ctx.interaction.response.send_message(embed=waiting_embed)
            try:
                await asyncio.wait_for(ctx.guild.chunk(), timeout=10)
                pass
            except asyncio.TimeoutError:
                pass
        else:
            await ctx.interaction.response.defer(thinking=True)
        ui = LeaderboardUI(self.bot, ctx.author, ctx.guild)
        await ui.run(ctx.interaction)


        await ui.wait()

    @cmds.hybrid_command(
        name=_p('cmd:achievements', 'achievements'),
        description=_p(
            'cmd:achievements|desc',
            "View your progress towards the activity achievement awards!"
        )
    )
    @appcmds.guild_only
    async def achievements_cmd(self, ctx: LionContext):
        if not ctx.guild:
            return
        if not ctx.interaction:
            return
        t = self.bot.translator.t

        await ctx.interaction.response.defer(thinking=True)

        achievements = await get_achievements_for(self.bot, ctx.guild.id, ctx.author.id)
        embed = discord.Embed(
            title=t(_p(
                'cmd:achievements|embed:title',
                "Achievements"
            )),
            colour=discord.Colour.orange()
        )
        for achievement in achievements:
            name, value = achievement.make_field()
            embed.add_field(
                name=name, value=value, inline=False
            )
        await ctx.reply(embed=embed)

    # Setting commands
    @LionCog.placeholder_group
    @cmds.hybrid_group('configure', with_app_command=False)
    async def configure_group(self, ctx: LionContext):
        ...

    @configure_group.command(
        name=_p('cmd:configure_statistics', "statistics"),
        description=_p('cmd:configure_statistics|desc', "Statistics configuration panel")
    )
    @appcmds.rename(
        season_start=_p('cmd:configure_statistics|param:season_start', "season_start")
    )
    @appcmds.describe(
        season_start=_p(
            'cmd:configure_statistics|param:season_start|desc',
            "Time from which to start counting activity for rank badges and season leaderboards. (YYYY-MM-DD)"
        )
    )
    @high_management_ward
    async def configure_statistics_cmd(self, ctx: LionContext,
                                       season_start: Optional[str] = None):
        t = self.bot.translator.t

        # Type checking guards
        if not ctx.guild:
            return
        if not ctx.interaction:
            return

        # Retrieve settings, using cache where possible
        setting_season_start = await self.settings.SeasonStart.get(ctx.guild.id)

        modified = []
        if season_start is not None:
            data = await setting_season_start._parse_string(ctx.guild.id, season_start)
            setting_season_start.data = data
            await setting_season_start.write()
            modified.append(setting_season_start)

        # Send update ack
        if modified:
            description = setting_season_start.update_message
            embed = discord.Embed(
                colour=discord.Colour.brand_green(),
                description=description
            )
            await ctx.reply(embed=embed)

        if ctx.channel.id not in StatisticsConfigUI._listening or not modified:
            # Launch setting group UI
            configui = StatisticsConfigUI(self.bot, ctx.guild.id, ctx.channel.id)
            await configui.run(ctx.interaction)
            await configui.wait()
