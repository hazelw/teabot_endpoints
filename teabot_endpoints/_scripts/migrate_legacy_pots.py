from teabot_endpoints.models import PotMaker, Claim


def migrate_legacy_pots():
    # Once upon a time we only cared about total weight and cups made per
    # PotMaker. Now we want to break them down into individual claims so
    # that we can have monthly/yearly leaderboards.
    for pot_maker in PotMaker.all():
        Claim.create(
            user=pot_maker, legacy=True, weight=pot_maker.total_weight_made,
            cups_made=pot_maker.number_of_cups_made
        )
