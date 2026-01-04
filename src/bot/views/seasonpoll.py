from discord import Interaction, Embed, ui, ButtonStyle

from src.base.config import config
from src.database.database import database
from src.utils.bar import get_bar


def get_poll_embed() -> Embed:
    continue_votes = database.votes.count_documents({"vote": "continue"})
    end_votes = database.votes.count_documents({"vote": "end"})
    total_votes = database.votes.count_documents({})
    bar_value = int((end_votes / total_votes) * 10) if total_votes > 0 else 0

    progress_bar = get_bar(value=bar_value, max_value=10)
    embed = Embed(
        color=config.colors["primary"],
        title="Season Poll",
        description=f"""\
How are you feeling about the current season so far?

Click the buttons below to cast an annonymous vote for what you would like to happen.
-# You can change your vote at any time by clicking a different button.


End - `{end_votes}` {progress_bar} `{continue_votes}` - Continue
-# {end_votes} out of {total_votes} votes to end the season.
""",
    )

    return embed


class PollView(ui.View):
    def __init__(self, *, message_id: int, state: dict):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.state = state

    @ui.button(label="End", style=ButtonStyle.danger, custom_id="seasonpoll:end")
    async def click(self, ctx: Interaction, button: ui.Button):
        vote_res = database.votes.update_one(
            {"user_id": ctx.user.id, "polltype": "seasonpoll"},
            {"$set": {"vote": "end"}},
            upsert=True,
        )

        if vote_res.matched_count == 0:
            self.state["votes"] = self.state.get("votes", 0) + 1
            database.views.update_one(
                {"message_id": self.message_id},
                {"$set": {"state": self.state}},
            )

        await ctx.response.edit_message(embed=get_poll_embed(), view=self)
        await ctx.response.send_message(
            f"Your vote to end the season has been recieved.", ephemeral=True
        )

    @ui.button(
        label="Continue", style=ButtonStyle.success, custom_id="seasonpoll:continue"
    )
    async def continue_button(self, ctx: Interaction, button: ui.Button):
        database.votes.update_one(
            {"user_id": ctx.user.id, "polltype": "seasonpoll"},
            {"$set": {"vote": "continue"}},
            upsert=True,
        )

        await ctx.response.edit_message(embed=get_poll_embed(), view=self)
        await ctx.response.send_message(
            f"Your vote to keep the season going has been recieved.", ephemeral=True
        )