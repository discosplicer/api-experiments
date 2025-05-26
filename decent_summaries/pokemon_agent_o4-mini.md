This Python module implements a fully autonomous, LLM-driven agent that plays a Game Boy–style emulator end to end via a PyBoy wrapper. On import, it configures Python logging, defines global constants (e.g. BASE_IMAGE_SIZE, MAX_TOKENS_OPENAI), and imports standard libraries (os, threading, json, time, pickle, base64, io, logging), numpy, PIL, typing helpers, and project-specific modules (config constants, prompt templates, API keys, emulator interface, tool definitions, and chat-message converters).

LocationCollisionMap maintains a dynamic per-zone 2D grid centered on the player, marking impassable tiles, sprites, and the player’s position. Its methods include:
- update_map(): pads and merges incoming local collision snapshots.
- compute_effective_distance_to_tiles(): breadth-first flood-fill to compute minimum-step distances.
- generate_buttons_to_coord(): backtracks the distance field into directional button presses.
- to_ascii(): renders richly annotated and simplified ASCII maps (legends, distances, sprite markers), logging the simpler maps to a rolling file.

TextDisplay implements a fixed-depth ring buffer (default 20) of recent messages. Each new message is printed and the full buffer serialized to text_output.txt, preserving a persistent dialogue log.

SimpleAgent encapsulates the core logic. Its constructor accepts the ROM path, headless/sound flags, LLM history-length settings, optional pickle-based state loading, and map-tracking toggles. It:
- Instantiates a PyBoy emulator.
- Selects one of Anthropic Claude, Google Gemini/GenAI, or OpenAI Chat as its LLM, with dedicated wrappers handling system prompts, retries, token logging, function calls, and format translation.
- Initializes separate “player” and “navigator” message histories, a bounded location history archive, the global collision map, boolean grids for explored tiles, multiple step counters (steps_completed, absolute_step_count, steps_since_checkpoint, steps_since_label_reset, steps_since_location_shift), a checkpoint list, and a TextDisplay.

The run() method ensures execution off PyBoy’s main thread, optionally restores a saved state, logs loop start, and enters a loop while self.running and steps_completed < num_steps. Each iteration:

1. Polls emulator.get_location() and get_coordinates(). On a new location, it logs “New Location,” labels the previous spot “Entrance to…,” updates milestones, resets all step counters, disables detailed navigator mode, and updates last_coords.

2. Captures a full-screen screenshot, overlays a 9×10 grid around the player (excluding their tile), annotates each grid cell with saved labels (via get_all_location_labels) or markers (“IMPASSABLE,” “EXPLORED,” “RECENTLY VISITED,” “CHECK HERE,” or “NPC/OBJECT” if a sprite is present), draws these labels onto the image, and encodes it as base64. Simultaneously, it downsamples the frame for collision-map resolution, extracts sprite positions, updates the global collision map (producing an ASCII rendering), and assembles an LLM prompt embedding these observations.

3. Prunes message histories:
   – In detailed navigator mode (and if not in combat), it strips old maps/images from navigator_message_history via strip_text_map_and_images_from_history and appends a new user message containing the ASCII map and screenshot.
   – Otherwise it retains only the last two messages, removes image or OpenAI “input_image” entries, replaces “[TEXT_MAP]…[/TEXT_MAP]” blocks with placeholders, and recursively prunes nested tool_results.

4. Invokes the configured LLM with the appropriate system or navigator prompt:
   – Claude: via Anthropic’s chat endpoint, with token logging and parsing of free-text and tool_use blocks.
   – Gemini: translating messages to Google’s format (including tool definitions), retrying on ServerError, and parsing text and tool calls.
   – OpenAI: via ChatCompletion, refreshing memory_info, location labels, coordinates, checkpoints, and the collision map before calls; pruning images afterward; retrying on BadRequestError; and extracting reasoning summaries, function/tool calls, and text.

5. Processes any returned tool_calls through process_tool_call(), which normalizes the tool_name per model and dispatches to appropriate handlers. It gathers tool_results, logs malformed calls, and—for OpenAI—appends function_call_output entries. In detailed navigator mode, if navigator history exceeds its max length, it triggers agentic_summary().

6. If no tool calls are returned, appends a fallback user message (“Can you please continue playing the game?”).

7. Updates multiple step counters, activates detailed navigator mode after 300 steps without location change, enables the location tracker after 50 steps since the last checkpoint, clears non-approximate labels if steps_since_label_reset exceeds thresholds (200 for Claude, 1000 for others), logs progress, updates the on-screen display, and periodically saves emulator state, label archives, and location milestones via save_location_archive().

8. Handles KeyboardInterrupt for a clean stop and catches other exceptions to log and re-raise; upon exit it saves the final state and stops the emulator.

Tool execution is managed by process_tool_call(), which routes to:
- press_buttons(buttons, wait, tool_id): issues the sequence, captures post-move memory state, location, and coordinates; updates location_history (bounded length) and the explored grid; gathers nearby labels; and returns a tool_result—either a simple acknowledgment for OpenAI or, for other models, detailed text summaries or annotated screenshots plus optional “[TEXT_MAP]” blocks.
- navigate_to(target_row, target_col): computes a local path via emulator.find_path, steps through it, updates state, captures a fresh screenshot, logs memory and map data, updates histories and trackers, retrieves saved labels, and returns a formatted tool_result.
- navigate_to_offscreen_coordinate(target_row, target_col): rejects unreachable targets or—if DIRECT_NAVIGATION is enabled—generates buttons via the full map; otherwise formulates a text-map query to distant-navigation tools, parses the resulting tool_use for a button sequence, and invokes press_buttons.
- bookmark_location_or_overwrite_label, mark_checkpoint, navigation_assistance, detailed_navigator: log or update archives or flags, reset counters or navigator histories, and return confirmations or assistance strings.
Unknown tools produce logged errors and error-containing tool_results.

Persistent state management is provided by:
- save_location_archive(pkl_path): pickles key agent variables (label_archive, location_history, both message histories, trackers, step counters, last_coords, map tool data, collision maps, checkpoints, navigation modes) via successive pickle.dump calls.
- load_location_archive(pkl_path): reverses this with nested try/except blocks for legacy compatibility; on FileNotFoundError it logs a warning, initializes fresh state, and sanitizes incomplete “tool_use” entries.

Ancillary utilities include:
- strip_text_map_and_images_from_history(message_history, openai_format=False): prunes all but the last two entries, removes image or input_image items, replaces “[TEXT_MAP]…[/TEXT_MAP]” with placeholders, and recursively processes nested tool_results.
- update_and_get_full_collision_map(location, coords): downsamples and merges the emulator’s collision snapshot into full_collision_map[location] and returns its ASCII rendering.
- get_all_location_labels(location): flattens saved labels at a location into coordinate–label pairs.
- navigation_assistance(navigation_goal): retrieves current location, coords, collision map, and labels; builds a mapping query; calls prompt_text_reply() with a navigation prompt; and displays the returned advice.
- prompt_text_reply(instructions, prompt, include_history, model, include_screenshot): optionally incorporates conversation history and a base64-encoded screenshot, transforms messages into the model’s API format (text, function calls, images), invokes the chat endpoint with retries, and returns concatenated text.
- agentic_summary(): gathers game state (RAM info, steps since events, ASCII map, checkpoints, labels, previous summary); constructs a multi-stage LLM prompt to extract raw facts, refine them, and produce a concise summary; logs each stage to agentic_summary.txt; captures a fresh screenshot; and replaces the message history with the final summary.

At startup, openai_message_history is seeded with a user message that interpolates the previous summary, mentions the current screenshot, and prompts continuation, plus an input_image entry referencing the base64 screenshot. The stop() method cleanly halts the agent by setting self.running = False and calling self.emulator.stop().

In the “if __name__ == '__main__'” block, the script computes rom_path as “pokemon.gb” one directory above its folder, instantiates SimpleAgent with that ROM, and in a try/except/finally it calls agent.run(num_steps=10), logs the number of steps completed, catches KeyboardInterrupt for manual stop, and ensures agent.stop() is invoked.