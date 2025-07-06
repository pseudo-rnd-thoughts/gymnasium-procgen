#include "../basic-abstract-game.h"
#include "../assetgen.h"
#include <set>
#include <queue>

const std::string NAME = "miner";

const float COMPLETION_BONUS = 10.0;
const int DIAMOND_REWARD = 1.0;

const int BOULDER = 1;
const int DIAMOND = 2;
const int MOVING_BOULDER = 3;
const int MOVING_DIAMOND = 4;
const int ENEMY = 5;
const int EXIT = 6;
const int DIRT = 9;

const int OOB_WALL = 10;

/**
### Description

Inspired by the classic game “BoulderDash”. The player, a robot, can dig through
dirt to move throughout the world. The world has gravity, and dirt supports
boulders and diamonds. Boulders and diamonds will fall through free space and
roll off each other. If a boulder or a diamond falls on the player, the game is
over. The goal is to collect all the diamonds in the level and then proceed
through the exit. The player receives a small reward for collecting a diamond
and a larger reward for completing the level.

### Action Space

The action space is `Discrete(15)` for which button combo to press.
The button combos are defined in [`env.py`](procgen/env.py).

The different combos are:

| Num | Combo        | Action          |
|-----|--------------|-----------------|
| 0   | LEFT + DOWN  | Move down-left  |
| 1   | LEFT         | Move left       |
| 2   | LEFT + UP    | Move up-left    |
| 3   | DOWN         | Move down       |
| 4   |              | Do Nothing      |
| 5   | UP           | Move up         |
| 6   | RIGHT + DOWN | Move down-right |
| 7   | RIGHT        | Move right      |
| 8   | RIGHT + UP   | Move up-right   |
| 9   | D            | Unused          |
| 10  | A            | Unused          |
| 11  | W            | Unused          |
| 12  | S            | Unused          |
| 13  | Q            | Unused          |
| 14  | E            | Unused          |

### Observation Space

The observation space is a box space with the RGB pixels the agent
sees in an `ndarray` of shape `(64, 64, 3)` with dtype `uint8`.

**Note**: If you are using the vectorized environment, the
observation space is a dictionary space where the pixels are under
the key "rgb".

### Rewards

A `+1` reward is given for each diamond collected.
A further `+10` is assigned after succesfully completing one
episode.

### Termination

The episode ends if any one of the following conditions is met:

1. The player reach the exit with collecting all the diamonds.
2. The player lose by getting crushed by a boulder or a diamond.
3. Timeout is reached.

### Known Issues

There is a low probability of unsolvable level configurations, with either a
diamond or the exit being unreachable.

*/

class MinerGame : public BasicAbstractGame {
  public:
    int diamonds_remaining = 0;

    MinerGame()
        : BasicAbstractGame(NAME) {
        main_width = 20;
        main_height = 20;

        mixrate = .5;
        maxspeed = .5;
        has_useful_vel_info = false;

        out_of_bounds_object = OOB_WALL;
        visibility = 8.0;
    }

    void load_background_images() override {
        main_bg_images_ptr = &platform_backgrounds;
    }

    void asset_for_type(int type, std::vector<std::string> &names) override {
        if (type == PLAYER) {
            names.push_back("misc_assets/robot_greenDrive1.png");
        } else if (type == BOULDER) {
            names.push_back("misc_assets/elementStone007.png");
        } else if (type == DIAMOND) {
            names.push_back("misc_assets/gemBlue.png");
        } else if (type == EXIT) {
            names.push_back("misc_assets/window.png");
        } else if (type == DIRT) {
            names.push_back("misc_assets/dirt.png");
        } else if (type == OOB_WALL) {
            names.push_back("misc_assets/tile_bricksGrey.png");
        }
    }

    bool is_blocked(const std::shared_ptr<Entity> &src, int target, bool is_horizontal) override {
        if (BasicAbstractGame::is_blocked(src, target, is_horizontal))
            return true;
        if (src->type == PLAYER && (target == BOULDER || target == MOVING_BOULDER || target == OOB_WALL))
            return true;

        return false;
    }

    bool will_reflect(int src, int target) override {
        return BasicAbstractGame::will_reflect(src, target) || (src == ENEMY && (target == BOULDER || target == DIAMOND || target == MOVING_BOULDER || target == MOVING_DIAMOND || target == out_of_bounds_object));
    }

    void handle_agent_collision(const std::shared_ptr<Entity> &obj) override {
        BasicAbstractGame::handle_agent_collision(obj);

        if (obj->type == ENEMY) {
            step_data.done = true;
        } else if (obj->type == EXIT) {
            if (diamonds_remaining == 0) {
                step_data.reward += COMPLETION_BONUS;
                step_data.level_complete = true;
                step_data.done = true;
            }
        }
    }

    int image_for_type(int type) override {
        if (type == MOVING_BOULDER) {
            return BOULDER;
        } else if (type == MOVING_DIAMOND) {
            return DIAMOND;
        }

        return BasicAbstractGame::image_for_type(type);
    }

    int get_agent_index() {
        return int(agent->y) * main_width + int(agent->x);
    }

    void set_action_xy(int move_action) override {
        BasicAbstractGame::set_action_xy(move_action);
        if (action_vx != 0)
            action_vy = 0;
    }

    void choose_new_vel(const std::shared_ptr<Entity> &ent) {
        int is_horizontal = rand_gen.randbool();
        int vel = rand_gen.randn(2) * 2 - 1;
        if (is_horizontal) {
            ent->vx = vel;
            ent->vy = 0;
        } else {
            ent->vx = 0;
            ent->vy = vel;
        }
    }

    void choose_world_dim() override {
        int dist_diff = options.distribution_mode;

        if (dist_diff == EasyMode) {
            main_width = 10;
            main_height = 10;
        } else if (dist_diff == HardMode) {
            main_width = 20;
            main_height = 20;
        } else if (dist_diff == MemoryMode) {
            main_width = 35;
            main_height = 35;
        }
    }

    void game_reset() override {
        BasicAbstractGame::game_reset();

        agent->rx = .5;
        agent->ry = .5;

        int main_area = main_height * main_width;

        options.center_agent = options.distribution_mode == MemoryMode;
        grid_step = true;

        float diamond_pct = 12 / 400.0f;
        float boulder_pct = 80 / 400.0f;

        int num_diamonds = (int)(diamond_pct * grid_size);
        int num_boulders = (int)(boulder_pct * grid_size);

        std::vector<int> obj_idxs = rand_gen.simple_choose(main_area, num_diamonds + num_boulders + 1);

        int agent_x = obj_idxs[0] % main_width;
        int agent_y = obj_idxs[0] / main_width;

        agent->x = agent_x + .5;
        agent->y = agent_y + .5;

        for (int i = 0; i < main_area; i++) {
            set_obj(i, DIRT);
        }

        for (int i = 0; i < num_diamonds; i++) {
            int cell = obj_idxs[i + 1];
            set_obj(cell, DIAMOND);
        }

        for (int i = 0; i < num_boulders; i++) {
            int cell = obj_idxs[i + 1 + num_diamonds];
            set_obj(cell, BOULDER);
        }

        std::vector<int> dirt_cells = get_cells_with_type(DIRT);

        set_obj(int(agent->x), int(agent->y), SPACE);

        for (int i = -1; i <= 1; i++) {
            for (int j = -1; j <= 1; j++) {
                int ox = agent_x + i;
                int oy = agent_y + j;
                if (get_obj(ox, oy) == BOULDER) {
                    set_obj(ox, oy, DIRT);
                }
            }
        }

        std::vector<int> exit_candidates;

        for (int cell : dirt_cells) {
            int above_obj = get_obj(cell + main_width);
            if (above_obj == DIRT || above_obj == out_of_bounds_object) {
                exit_candidates.push_back(cell);
            }
        }

        fassert(exit_candidates.size() > 0);

        int exit_cell = exit_candidates[rand_gen.randn((int)(exit_candidates.size()))];
        set_obj(exit_cell, SPACE);
        auto exit = add_entity((exit_cell % main_width) + .5, (exit_cell / main_width) + .5, 0, 0, .5, EXIT);
        exit->render_z = -1;
    }

    int get_moving_type(int type) {
        if (type == DIAMOND)
            return MOVING_DIAMOND;
        if (type == BOULDER)
            return MOVING_BOULDER;

        return type;
    }

    bool is_moving(int type) {
        return type == MOVING_BOULDER || type == MOVING_DIAMOND;
    }

    int get_stationary_type(int type) {
        if (type == MOVING_DIAMOND)
            return DIAMOND;
        if (type == MOVING_BOULDER)
            return BOULDER;

        return type;
    }

    bool is_free(int idx) {
        return get_obj(idx) == SPACE && (get_agent_index() != idx);
    }

    bool is_round(int type) {
        return type == BOULDER || type == MOVING_BOULDER || type == DIAMOND || type == MOVING_DIAMOND;
    }

    void handle_push() {
        int agent_idx = get_agent_index();
        int agentx = agent_idx % main_width;

        if (action_vx == 1 && (agent->vx == 0) && (agentx < main_width - 2) && get_obj(agent_idx + 1) == BOULDER && get_obj(agent_idx + 2) == SPACE) {
            set_obj(agent_idx + 1, SPACE);
            set_obj(agent_idx + 2, BOULDER);
            agent->x += 1;
        } else if (action_vx == -1 && (agent->vx == 0) && (agentx > 1) && get_obj(agent_idx - 1) == BOULDER && get_obj(agent_idx - 2) == SPACE) {
            set_obj(agent_idx - 1, SPACE);
            set_obj(agent_idx - 2, BOULDER);
            agent->x -= 1;
        }
    }

    void game_step() override {
        BasicAbstractGame::game_step();

        if (action_vx > 0)
            agent->is_reflected = false;
        if (action_vx < 0)
            agent->is_reflected = true;

        handle_push();

        int agent_obj = get_obj(int(agent->x), int(agent->y));

        if (agent_obj == DIAMOND) {
            step_data.reward += DIAMOND_REWARD;
        }

        if (agent_obj == DIRT || agent_obj == DIAMOND) {
            set_obj(int(agent->x), int(agent->y), SPACE);
        }

        int main_area = main_width * main_height;

        int diamonds_count = 0;

        for (int idx = 0; idx < main_area; idx++) {
            int obj = get_obj(idx);

            int obj_x = idx % main_width;
            int agent_idx = (agent->y - .5) * main_width + (agent->x - .5);

            int stat_type = get_stationary_type(obj);

            if (stat_type == DIAMOND) {
                diamonds_count++;
            }

            if (obj == BOULDER || obj == MOVING_BOULDER || obj == DIAMOND || obj == MOVING_DIAMOND) {
                int below_idx = idx - main_width;
                int obj2 = get_obj(below_idx);
                bool agent_is_below = agent_idx == below_idx;

                if (obj2 == SPACE && !agent_is_below) {
                    set_obj(idx, SPACE);
                    set_obj(below_idx, get_moving_type(obj));
                } else if (agent_is_below && is_moving(obj)) {
                    step_data.done = true;
                } else if (is_round(obj2) && obj_x > 0 && is_free(idx - 1) && is_free(idx - main_width - 1)) {
                    set_obj(idx, SPACE);
                    set_obj(idx - 1, get_stationary_type(obj));
                } else if (is_round(obj2) && obj_x < main_width - 1 && is_free(idx + 1) && is_free(idx - main_width + 1)) {
                    set_obj(idx, SPACE);
                    set_obj(idx + 1, stat_type);
                } else {
                    set_obj(idx, stat_type);
                }
            }
        }

        diamonds_remaining = diamonds_count;

        for (auto ent : entities) {
            if (ent->type == ENEMY) {
                if (rand_gen.randn(6) == 0) {
                    choose_new_vel(ent);
                }
            }
        }
    }

    void serialize(WriteBuffer *b) override {
        BasicAbstractGame::serialize(b);
        b->write_int(diamonds_remaining);
    }

    void deserialize(ReadBuffer *b) override {
        BasicAbstractGame::deserialize(b);
        diamonds_remaining = b->read_int();
    }
};

REGISTER_GAME(NAME, MinerGame);
