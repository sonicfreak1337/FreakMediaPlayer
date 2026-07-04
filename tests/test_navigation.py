from freak_media_player.ui.navigation import NavigationSection, NavigationViewModel


def test_navigation_defaults_to_library() -> None:
    navigation = NavigationViewModel()

    assert navigation.selected_section == NavigationSection.LIBRARY


def test_navigation_only_shows_currently_usable_sections() -> None:
    navigation = NavigationViewModel()

    assert [item.section for item in navigation.items] == [
        NavigationSection.LIBRARY,
        NavigationSection.PLAYLISTS,
        NavigationSection.EQUALIZER,
    ]


def test_navigation_selects_section() -> None:
    navigation = NavigationViewModel()

    navigation.select(NavigationSection.EQUALIZER)

    assert navigation.selected_section == NavigationSection.EQUALIZER
