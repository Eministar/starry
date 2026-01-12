import discord


class RatingCommentModal(discord.ui.Modal):
    def __init__(self, service, ticket_id: int, rating: int):
        super().__init__(title=f"Bewertung: {rating} ⭐")
        self.service = service
        self.ticket_id = int(ticket_id)
        self.rating = int(rating)

        self.comment = discord.ui.TextInput(
            label="Kommentar (optional)",
            required=False,
            max_length=500,
            style=discord.TextStyle.paragraph,
            placeholder="Wenn du magst: kurz sagen was gut/schlecht war.",
        )
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        text = (self.comment.value or "").strip()
        await self.service.submit_rating(interaction, self.ticket_id, self.rating, text if text else None)


class RatingView(discord.ui.View):
    def __init__(self, service, ticket_id: int):
        super().__init__(timeout=600)
        self.service = service
        self.ticket_id = int(ticket_id)

        for r in range(1, 6):
            btn = discord.ui.Button(
                custom_id=f"starry:rating:{ticket_id}:{r}",
                style=discord.ButtonStyle.primary,
                label=("⭐" * r),
            )
            btn.callback = self._make_cb(r)
            self.add_item(btn)

    def _make_cb(self, rating: int):
        async def _cb(interaction: discord.Interaction):
            await interaction.response.send_modal(RatingCommentModal(self.service, self.ticket_id, rating))
        return _cb
