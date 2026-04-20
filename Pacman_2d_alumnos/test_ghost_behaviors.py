from types import SimpleNamespace

import numpy as np

from Ghost import Ghost, NavigationGraph


MC = [[0] * 10 for _ in range(10)]
XPxToMC = np.zeros(359, dtype=int)
YPxToMC = np.zeros(361, dtype=int)
VIEW = 400.0


def test_ghost_euclid_recorre_hacia_pacman():
    mapa = np.zeros((120, 120), dtype=int)
    nav = NavigationGraph(mapa, view_size=VIEW, actor_radius=Ghost.NAV_RADIUS, step=Ghost.NAV_STEP)
    ghost = Ghost(
        mapa,
        MC,
        XPxToMC,
        YPxToMC,
        180.0,
        200.0,
        0.0,
        "euclid",
        view_size=VIEW,
        navigator=nav,
        house_exit_xy=(180.0, 200.0),
    )
    pacman = SimpleNamespace(px=300.0, py=200.0, angle=0.0)

    before_x = ghost.px
    for _ in range(4):
        ghost.update2(pacman, [ghost])

    assert ghost.px > before_x


def test_ghost_astar_rodea_un_muro_para_llegar_al_objetivo():
    mapa = np.zeros((120, 120), dtype=int)
    mapa[:, 58:62] = 1
    mapa[54:66, 58:62] = 0
    nav = NavigationGraph(mapa, view_size=VIEW, actor_radius=Ghost.NAV_RADIUS, step=Ghost.NAV_STEP)
    ghost = Ghost(mapa, MC, XPxToMC, YPxToMC, 90.0, 200.0, 0.0, "astar_lead", view_size=VIEW, navigator=nav)
    pacman = SimpleNamespace(px=320.0, py=200.0, angle=0.0)

    goal = ghost._astar_goal(pacman, [ghost])
    route = ghost._plan_astar(pacman, [ghost])

    assert route, "A* no produjo ruta"
    assert route[-1] == goal


def test_ghosts_astar_cooperativos_no_persiguen_el_mismo_nodo():
    mapa = np.zeros((120, 120), dtype=int)
    nav = NavigationGraph(mapa, view_size=VIEW, actor_radius=Ghost.NAV_RADIUS, step=Ghost.NAV_STEP)
    lead = Ghost(mapa, MC, XPxToMC, YPxToMC, 180.0, 180.0, 0.0, "astar_lead", view_size=VIEW, navigator=nav)
    support = Ghost(mapa, MC, XPxToMC, YPxToMC, 220.0, 220.0, 0.0, "astar_support", view_size=VIEW, navigator=nav)
    pacman = SimpleNamespace(px=260.0, py=200.0, angle=0.0)

    lead_goal = lead._astar_goal(pacman, [lead, support])
    support_goal = support._astar_goal(pacman, [lead, support])
    lead_route = lead._plan_astar(pacman, [lead, support])
    lead.route = lead_route
    support_route = support._plan_route(pacman, [lead, support])

    assert lead_goal != support_goal
    assert support_route, "el fantasma cooperativo no encontró ruta"
    assert support_route[:5] != lead_route[:5]


def test_ghost_release_delay_mantiene_al_fantasma_en_casa():
    mapa = np.zeros((120, 120), dtype=int)
    nav = NavigationGraph(mapa, view_size=VIEW, actor_radius=Ghost.NAV_RADIUS, step=Ghost.NAV_STEP)
    ghost = Ghost(
        mapa,
        MC,
        XPxToMC,
        YPxToMC,
        180.0,
        180.0,
        0.0,
        "euclid",
        view_size=VIEW,
        navigator=nav,
        release_delay_ms=120,
        house_exit_xy=(200.0, 140.0),
    )
    pacman = SimpleNamespace(px=320.0, py=200.0, angle=0.0)

    start = (ghost.px, ghost.py)
    ghost.update2(pacman, [ghost], dt_ms=50)
    ghost.update2(pacman, [ghost], dt_ms=50)

    assert (ghost.px, ghost.py) == start
    assert ghost.state == "waiting"
    ghost.update2(pacman, [ghost], dt_ms=20)
    assert ghost.state == "exiting"
    ghost.update2(pacman, [ghost], dt_ms=16)
    assert (ghost.px, ghost.py) != start
