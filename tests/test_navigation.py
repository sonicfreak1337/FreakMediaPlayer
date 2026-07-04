from freak_media_player.ui.navigation import NavigationSection, NavigationViewModel


def test_navigation_defaults_to_library() -> None:
    navigation = NavigationViewModel()

    assert navigation.selected_section == NavigationSection.LIBRARY


def test_navigation_selects_section() -> None:
    navigation = NavigationViewModel()

    navigation.select(NavigationSection.EQUALIZER)

    assert navigation.selected_section == NavigationSection.EQUALIZER
