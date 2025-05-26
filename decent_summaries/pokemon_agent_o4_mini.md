Below is a consolidated, information-dense specification of the emulator-LLM agent and its support classes, suitable for ingestion by a downstream AI.

1. Imports & Configuration  
• Python stdlibs: base64, json, logging, threading, time, os, io, shutil  
• Third-party: numpy; PIL (Image, ImageDraw, ImageFont); PyBoy emulator wrapper; Anthropic, Gemini, OpenAI SDKs  
• On import: configure Python logging; set BASE_IMAGE_SIZE=(160,144), MAX_TOKENS_OPENAI=50000  

2. Class: LocationCollisionMap  
• Fields: infinite, player-centered grid of tile codes (–1 unknown, 0 impassable, 1 passable, 2 sprite, 3 player), row/col offsets, BFS distance map  
• __init__(initial_slice, sprites, player_pos): center-embeds 9×10 slice, place sprites/player, init distances  
• update_map(new_slice, sprites, player_pos): pad & shift when near edges, write new slice/positions, recompute BFS distances from player  
• generate_buttons_to_coord(target): backtrack along strictly decreasing distances to emit “up/down/left/right” moves  
• to_ascii(visited_overlay=False) / make_ascii_segment: render compact or detailed ASCII map (logs detailed to mapping_log.txt), return LLM-friendly string  

3. Class: TextDisplay  
• Maintains a timestamped rolling buffer of the last N messages (default 20)  
• add_message(msg): log via Python logging, drop oldest if full, overwrite text_output.txt with buffer  

4. Class: SimpleAgent  

  4.1 Initialization (__init__)  
  • Launch headless, sound-enabled, threaded PyBoy emulator pointing at given ROM  
  • Instantiate LLM client (Anthropic, Gemini or OpenAI) with credentials  
  • Initialize:  
    – message_history & navigator_message_history (including OpenAI-formatted variants)  
    – location_history (recent coords), label_archive (per-tile labels), per-location LocationCollisionMap instances  
    – navigation modes (direct vs. LLM-assisted), detailed navigator flag, checkpoints list, action counters  
    – TextDisplay for user/system messages  
  • Optionally load saved emulator state & archives (with backward-compat; drop trailing tool_use records on load)  

  4.2 Core Utilities  
  • get_screenshot_base64(): capture & downsize framebuffer to BASE_IMAGE_SIZE; overlay coordinate grid & multiline labels via PIL; save “test.png”; return base64 PNG  
  • save_location_archive(path) / load_location_archive(path): pickle/unpickle label_archive, histories, maps, counters; warn on missing  
  • strip_text_map_and_images_from_history(history, openai_format=False): remove embedded images and “[TEXT_MAP]…[/TEXT_MAP]” blocks; reformat for OpenAI if requested  
  • update_and_get_full_collision_map(location, coords, visited_overlay=False): fetch fresh 9×10 slice; retrieve/create corresponding LocationCollisionMap; update_map; return ASCII map  
  • get_all_location_labels(location): case-insensitive lookup in label_archive; return list of ((col,row), label)  

  4.3 Actuation & Tool-Call Processing  
  • press_buttons(buttons:list, wait:bool=False, tool_id=None) → tool_result:  
    – Log & send button sequence to emulator; update last_coords & trim location_history; mark tile visited if tracker active; gather nearby labels  
    – Return either simple text confirmation or (in navigator modes) dict with screenshot, memory_info, labels, recent path, checkpoints, step count, optional combat notice, full ASCII map wrapped in [TEXT_MAP]…[/TEXT_MAP]  
  • process_tool_call(raw_call): parse tool_name, inputs, tool_id; dispatch to:  
    – press_buttons  
    – navigate_to (on-screen pathfinding via emulator.find_path)  
    – navigate_to_offscreen_coordinate (DIRECT via generate_buttons_to_coord or LLM-planned with retries)  
    – bookmark_location_or_overwrite_label  
    – mark_checkpoint  
    – navigation_assistance  
    – detailed_navigator  
    – unknown tool: log error; return error result  

  4.4 Main Loop: run(num_steps=1, save_every=10, save_file_name=None, _running_in_thread=False)  
  • If on main thread and not threaded: spawn new Thread to init emulator and re-invoke run(); return immediately  
  • Log “Starting agent loop”; if loading state, restore it into emulator  
  • While running and steps_completed < num_steps:  
    1. Poll emulator for current location & coords; on first visit announce milestone, record all_visited_locations  
    2. Update last_coords  
    3. Build LLM input: choose detailed navigator vs. general history; strip old visuals; mark last and third-last user messages as ephemeral if history ≥3  
    4. Invoke LLM (Anthropic, Gemini or OpenAI) with up to 2 retries: log tokens; extract reasoning, tool_calls, assistant_content; display via TextDisplay  
    5. Post-response: append assistant_content; if tool_calls, process each and collect results; else inject fallback “Can you please continue playing the game?”  
    6. Increment counters (steps_completed, absolute_step_count, steps_since_checkpoint, steps_since_label_reset, steps_since_location_shift); trigger:  
       – steps_since_location_shift >300 → activate detailed navigator  
       – steps_since_checkpoint >50 → activate location tracker  
       – location change detected → archive “Entrance to X” label for previous coords; reset counters; disable detailed navigator; notify histories  
       – steps_since_label_reset > threshold (200 for Claude, 1000 otherwise) → clear non-approximate labels  
    7. Persist: every save_every steps pickle agent state; catch KeyboardInterrupt to stop; log and re-raise other exceptions; on exit final save and stop emulator thread  

5. navigation_assistance(navigation_goal)  
• Retrieve current emulator state; update full collision map; gather all labels; construct mapping query (ASCII map, labels, goal); call prompt_text_reply(NAVIGATION_PROMPT); return LLM guidance  

6. prompt_text_reply(instructions, prompt, include_history=True, model, include_screenshot=False)  
• Optionally deep-copy and mark recent user messages as ephemeral; if include_screenshot, capture/upscale screenshot with coords overlay, embed as base64  
• Model calls:  
  – Claude: build user message (text + optional image); call Anthropic API; concatenate text blocks  
  – Gemini: format as Google chat “Parts,” set tools; chat with up to 2 retries; join response parts  
  – OpenAI: append input_text/input_image to openai_message_history; call function-calling API; extract output text from streaming chunks  

7. agentic_summary()  
• Log entry; retrieve RAM info, location, coords, previous summary, last 10 checkpoints, all labels  
• Build composite prompt with memory info, step counters, ASCII map (or “Not yet available” if in combat), labels, previous summary, screenshot  
• Run three sequential LLM passes via prompt_text_reply: (1) extract “Facts,” (2) “Clean Facts,” (3) final summarization; write all stages to agentic_summary.txt; display final summary; replace message_history with only the final summary  

8. Post-summary Message Update  
• Append to message sequence a “Current game screenshot for reference:” text block, embed the base64-encoded PNG, and prompt the model to continue playing by selecting its next action.  

9. openai_message_history Initialization  
• After summarization, set self.openai_message_history to a single “user” entry containing a two-element list:  
  1. input_text: concatenation of the prior conversation summary, note of current screenshot, and instruction to continue playing  
  2. input_image: data URL pointing to the same screenshot  

10. stop() Method  
• Defines stop(): sets self.running=False and calls self.emulator.stop() to halt the emulator thread  

11. Main Script Guard  
Under “if __name__ == '__main__'”:  
• Compute path to “pokemon.gb” relative to script directory  
• Instantiate SimpleAgent with that ROM path  
• Invoke agent.run(num_steps=10), logging steps completed  
• Catch KeyboardInterrupt to log interrupt message  
• In finally block ensure agent.stop() is always called