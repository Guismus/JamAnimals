# Game configuration and level definitions for WildChain: Apex Hunt

ARENA_WIDTH = 2400
ARENA_HEIGHT = 2400
DAY_NIGHT_DURATION = 30 * 60 # 30 seconds at 60 FPS

LEVEL_CONFIGS = [
    {
        "name": "Level 1: The Bridges Crossing",
        "rabbits_needed": 5,
        "description": "A horizontal river cuts the forest in half. Wolves guard the two bridges.",
        "portal_pos": (1200, 900),
        "lakes": [
            {"x": 1200, "y": 1200, "w": 2400, "h": 220, "shape": "rect", "r": 0}
        ],
        "bridges": [
            {"x": 600, "y": 1200, "w": 140, "h": 260, "shape": "rect", "r": 0},
            {"x": 1800, "y": 1200, "w": 140, "h": 260, "shape": "rect", "r": 0}
        ]
    },
    {
        "name": "Level 2: The Sacred Isle",
        "rabbits_needed": 5,
        "description": "A deep circular lake surrounds a central island. Four bridges lead to the center.",
        "portal_pos": (1200, 1200),
        "lakes": [
            {"x": 1200, "y": 1200, "w": 0, "h": 0, "shape": "circle", "r": 340}
        ],
        "bridges": [
            # Central Island
            {"x": 1200, "y": 1200, "w": 0, "h": 0, "shape": "circle", "r": 120},
            # Bridges (lengthened to 260 to bridge the 220px water ring and overlap the central island)
            {"x": 1200, "y": 970, "w": 90, "h": 260, "shape": "rect", "r": 0},
            {"x": 1200, "y": 1430, "w": 90, "h": 260, "shape": "rect", "r": 0},
            {"x": 970, "y": 1200, "w": 260, "h": 90, "shape": "rect", "r": 0},
            {"x": 1430, "y": 1200, "w": 260, "h": 90, "shape": "rect", "r": 0}
        ]
    },
    {
        "name": "Level 3: The Canal Labyrinth",
        "rabbits_needed": 5,
        "description": "Multiple streams partition the clearing. Navigate the bridge network to escape.",
        "portal_pos": (1200, 1200),
        "lakes": [
            {"x": 1200, "y": 700, "w": 2400, "h": 120, "shape": "rect", "r": 0},
            {"x": 1200, "y": 1700, "w": 2400, "h": 120, "shape": "rect", "r": 0},
            {"x": 1200, "y": 1200, "w": 120, "h": 2400, "shape": "rect", "r": 0}
        ],
        "bridges": [
            {"x": 600, "y": 700, "w": 120, "h": 160, "shape": "rect", "r": 0},
            {"x": 1800, "y": 700, "w": 120, "h": 160, "shape": "rect", "r": 0},
            {"x": 600, "y": 1700, "w": 120, "h": 160, "shape": "rect", "r": 0},
            {"x": 1800, "y": 1700, "w": 120, "h": 160, "shape": "rect", "r": 0},
            {"x": 1200, "y": 400, "w": 160, "h": 120, "shape": "rect", "r": 0},
            {"x": 1200, "y": 2000, "w": 160, "h": 120, "shape": "rect", "r": 0},
            {"x": 1200, "y": 1200, "w": 160, "h": 320, "shape": "rect", "r": 0}
        ]
    }
]
