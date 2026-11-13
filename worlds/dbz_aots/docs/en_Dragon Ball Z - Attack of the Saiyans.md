# Dragon Ball Z - Attack of the Saiyans

## Status

This world covers the whole story: all 219 chests of the game (6 of them with the `east_city_ruins` option), its two
trap chests, all 19 hidden items, the four rewards of the carrot man, the end of each chapter and the three story
scenes that give a key item.

## What does randomization do to this game?

The items found in chests and hidden spots are shuffled into the multiworld. Taking one sends a check; items
received from other players are added directly to your inventory.

## What is the goal?

By default, defeat Vegeta in the last battle of the game (end of chapter 15). The goal is sent when the scene that
follows this battle starts. There is no save after the final battle, so do everything else before it.

With the `goal_chapter` option, the game can end earlier: the goal is sent when the next chapter starts, and only the
locations up to that chapter are included.

With `goal: broly`, defeat Broly, the secret boss, instead. After Nappa and before the last battle against Vegeta,
Mr. Popo makes the Dragon Balls again: collect them, pick Shenron's wish "To fight the ultimate enemy", then enter the
portal at the top of East Mt. Paozu (Dragon Rock). The goal is sent when the scene after the victory starts (you also
receive Broly's Necklace). Broly is level 95 with 85,000 HP: be well prepared. Do it before the final battle, since
there is no save after it.

## Which locations are randomized?

256 locations:

- the chests of every area of the story, from Training Island to Gizard Wasteland (211), and the trap chest of
  Princess Snake's House, which starts a battle (1);
- the optional Sewer under the Martial Arts Temple, with the `key_items` option: two chests and a trap chest (3);
- the hidden items you get by examining a drawer, a stall, the back of a car, a ghost... (19);
- the rewards of the carrot man of West City for 1, 100, 500 and 1000 carrots, with the `carrot_rewards` option (4,
  the last one only with `key_items`). They never hold anything important: collecting 1000 carrots takes long;
- the end of the prologue and of chapters 1 to 14 (15);
- the three story scenes that give a key item, with the `key_items` option (3).

20 of those chests and hidden items are off the story path (some under a rock to break with a Ki blast). The logic
expects them during the tour before the final battle (chapter 15), when the Dragon Ball hunt brings you back to
every area.

The 6 chests of East City Ruins are added with the `east_city_ruins` option; reaching them needs the 7 Dragon
Balls and Shenron's wish "To Go Somewhere New".

The story closes some areas for a while: the Other World (including the Underworld) after chapter 9 (until chapter
13) and maybe Nemuria Ruins after chapter 11. Their locations never hold progression items, so a chest left behind there never blocks
anyone. Location groups are available for hints: one per area (for example "Kiwi Volcano") and "Story".

## Which items can be found?

The original contents of those chests and hidden spots: healing items, stat fruits, accessories and capsules,
plus filler for the chapter ends. Seven of them matter for progression:

- **Gas Mask** (capsule): needed from the prologue. On Training Island, Bulma lets nobody into the poison mist until
  the Gas Mask is equipped, and the end of the prologue is behind it; the Spinach Wastes (chapter 6) cross a gas
  floor too. By default it is in one of your own first locations (option `gas_mask_placement`).
- **Snowfield Key** (key item, with the `key_items` option): opens the Holly Plain gate on the story path of chapter
  8. Lunch's scene no longer gives it: it comes from the multiworld like any other item.
- **Submarine** (key item, with the `key_items` option): gets the party into the Pirate Cave in chapter 10. The
  scene at Capsule Corp. no longer gives it.
- **Bubbles' Thing** (key item, with the `key_items` option): repairs the five stumps of Yemma Forest in chapter 13.
  The scene on King Kai's Planet no longer gives it.
- **Sewer Key** (key item, with the `key_items` option): opens the manhole of the Martial Arts Temple, the only way
  into the Sewer. The game gives it for 1000 carrots; the logic expects the Sewer during the tour before the final
  battle (chapter 15). The carrot man no longer gives it: his 1000-carrot reward is a location instead.
- **Ki-Blast Fruit** (4 in the pool, 2 needed): use it from the Items menu to raise your Ki-blast meter. One fruit breaks the
  level 2 rocks that block the story in chapter 8, two fruits break the level 3 doors of chapter 13.

Received items are not used or equipped automatically: use the fruits and equip the capsules yourself.

## Options

- `goal` (`chapter` or `broly`, default `chapter`): what wins the game (see above).
- `goal_chapter` (1 to 15, default 15): with `goal: chapter`, the chapter whose end wins the game.
- `hidden_items` (default on): include the 19 hidden items.
- `chapter_checks` (default on): the end of the prologue and of each chapter before the goal sends a check.
- `key_items` (default on): shuffle the Snowfield Key, the Submarine and Bubbles' Thing (the three story scenes
  that give them become locations) and the Sewer Key (which adds the Sewer).
- `carrot_rewards` (default on): the four rewards of the carrot man of West City are locations, holding only filler.
- `east_city_ruins`: add the 6 chests of East City Ruins (see above).
- `gas_mask_placement` (default `own_early`): where the Gas Mask can be. `own_early`: in one of your own first
  locations (Kame House and Training Island, before the mist); `any_early`: in the first locations of any world;
  `start`: in your starting inventory; `anywhere`: wherever the logic allows (in another world, it can come late).
- `experience_multiplier` (1 to 10): multiply the experience and AP earned in battle. The client adds the extra
  after each battle; it never makes a character skip a level at once, the rest is added after the next battles.
- `death_link`: when every fighter of your party falls in battle, everyone linked dies too. When someone else
  dies, the HP of your fighters drop to 0 at the start of your next battle, which ends it in a defeat (back to the
  title screen: you continue from your last save).

## Supported version

Only the European release (game code `BRPP`, revision 0) is supported. It has only been tested in French.
