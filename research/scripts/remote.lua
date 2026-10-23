-- Télécommande de BizHawk pour la recherche (DBZ: Attack of the Saiyans, cœur melonDS).
--
-- Le script lit les ordres écrits dans REMOTE_DIR/cmd.txt (par research/scripts/remote.py, côté WSL),
-- les exécute dans l'émulateur, puis écrit le compte rendu dans REMOTE_DIR/done.txt.
-- Première ligne de cmd.txt : « id <nombre> » ; ensuite un ordre par ligne :
--   press <boutons> <images>   maintenir des boutons (ex. « A », « Up+B ») pendant n images, puis relâcher
--   wait <images>              laisser tourner le jeu n images (60 images = 1 seconde)
--   shot <nom>                 capture d'écran -> REMOTE_DIR/<nom>.png
--   dump <nom>                 photo de Main RAM -> DUMP_DIR/<nom>.bin
--   read <adresse> <taille>    lire des octets de Main RAM (adresse en hexadécimal, ex. 0CC398)
--   write <adresse> <octets>   écrire des octets en hexadécimal (ex. « write 0CDB80 C8 00 00 00 »)
--   save <emplacement>         état de sauvegarde dans l'emplacement 0-9
--   load <emplacement>         charger l'état de sauvegarde 0-9
--   touch <x> <y> <images>     toucher l'écran tactile en (x, y)
--   buttons                    lister les noms des boutons de la manette
--   frame                      numéro de l'image en cours
-- Il n'écrit dans la mémoire du jeu que sur un ordre « write », réservé aux expériences de recherche dans les
-- emplacements d'état de Claude (7, 8, 9), jamais dans une partie du joueur.
-- Les états de sauvegarde faits à la main (Shift+F<n>) prennent toujours une photo mémoire, comme dump_ram.lua.

local REMOTE_DIR = "C:/Users/Aurelien/Desktop/archipelago/dbz_research/remote/"
local DUMP_DIR = "C:/Users/Aurelien/Desktop/archipelago/dbz_research/dumps/"
local DOMAIN = "Main RAM"
local READ_SIZE = 65536
local WRITE_SIZE = 4096
local POLL_EVERY = 10 -- images entre deux lectures de cmd.txt

local last_id = nil
local queue = {}
local log = {}
local current_id = nil
local hold = nil -- { buttons = {...}, frames = n, release = n }
local waiting = 0

local function note(text)
    log[#log + 1] = text
end

local function dump(name)
    local size = memory.getmemorydomainsize(DOMAIN)
    local file = io.open(DUMP_DIR .. name .. ".bin", "wb")
    if file == nil then
        note("ERREUR dump : impossible d'écrire " .. name)
        return
    end
    for address = 0, size - 1, READ_SIZE do
        local bytes = memory.read_bytes_as_array(address, math.min(READ_SIZE, size - address), DOMAIN)
        for first = 1, #bytes, WRITE_SIZE do
            file:write(string.char(table.unpack(bytes, first, math.min(first + WRITE_SIZE - 1, #bytes))))
        end
    end
    file:close()
    note(string.format("dump %s ok (image %d)", name, emu.framecount()))
end

local function split(text)
    local words = {}
    for word in text:gmatch("%S+") do
        words[#words + 1] = word
    end
    return words
end

-- Exécute un ordre instantané, ou prépare un ordre qui dure plusieurs images (press, wait, touch).
local function run_order(words)
    local order = words[1]
    if order == "press" then
        local buttons = {}
        for button in words[2]:gmatch("[^+]+") do
            buttons[button] = true
        end
        hold = { buttons = buttons, frames = tonumber(words[3]) or 1, release = 4 }
    elseif order == "wait" then
        waiting = tonumber(words[2]) or 1
    elseif order == "shot" then
        client.screenshot(REMOTE_DIR .. words[2] .. ".png")
        note("shot " .. words[2] .. " ok")
    elseif order == "dump" then
        dump(words[2])
    elseif order == "read" then
        local bytes = memory.read_bytes_as_array(tonumber(words[2], 16), tonumber(words[3]), DOMAIN)
        local hex = {}
        for i = 1, #bytes do
            hex[i] = string.format("%02X", bytes[i])
        end
        note("read " .. words[2] .. " : " .. table.concat(hex, " "))
    elseif order == "write" then
        local bytes = {}
        for i = 3, #words do
            bytes[#bytes + 1] = tonumber(words[i], 16)
        end
        memory.write_bytes_as_array(tonumber(words[2], 16), bytes, DOMAIN)
        note("write " .. words[2] .. " ok")
    elseif order == "save" then
        savestate.saveslot(tonumber(words[2]))
        note("save " .. words[2] .. " ok")
    elseif order == "load" then
        savestate.loadslot(tonumber(words[2]))
        note("load " .. words[2] .. " ok")
    elseif order == "touch" then
        hold = { buttons = { Touch = true }, frames = tonumber(words[4]) or 2, release = 4,
                 analog = { ["Touch X"] = tonumber(words[2]), ["Touch Y"] = tonumber(words[3]) } }
    elseif order == "buttons" then
        local names = {}
        for name, _ in pairs(joypad.get()) do
            names[#names + 1] = name
        end
        table.sort(names)
        note("buttons : " .. table.concat(names, ", "))
    elseif order == "frame" then
        note("frame " .. emu.framecount())
    elseif order ~= nil then
        note("ordre inconnu : " .. order)
    end
end

-- Exécute les ordres instantanés ; s'arrête sur un ordre qui dure plusieurs images.
-- Un ordre mal écrit (ex. « press » sans bouton) est signalé dans le compte rendu au lieu d'arrêter le script.
local function run_queue()
    while hold == nil and waiting == 0 and #queue > 0 do
        local line = table.remove(queue, 1)
        local ok, problem = pcall(run_order, split(line))
        if not ok then
            note("ERREUR « " .. line .. " » : " .. tostring(problem))
        end
    end
    if hold == nil and waiting == 0 and #queue == 0 and current_id ~= nil then
        note("frame " .. emu.framecount())
        local done = io.open(REMOTE_DIR .. "done.txt", "w")
        done:write("id " .. current_id .. "\n" .. table.concat(log, "\n") .. "\n")
        done:close()
        current_id = nil
    end
end

local function poll()
    local file = io.open(REMOTE_DIR .. "cmd.txt", "r")
    if file == nil then
        return
    end
    local lines = {}
    for line in file:lines() do
        lines[#lines + 1] = line
    end
    file:close()
    local id = lines[1] and lines[1]:match("^id (%d+)")
    if id == nil or id == last_id then
        return
    end
    last_id = id
    current_id = id
    log = {}
    queue = {}
    for i = 2, #lines do
        if lines[i]:match("%S") then
            queue[#queue + 1] = lines[i]
        end
    end
end

local photo_number = 0
event.onsavestate(function()
    photo_number = photo_number + 1
    dump(string.format("manuel_%02d", photo_number))
end, "photo_memoire")

print("Télécommande prête. Dossier : " .. REMOTE_DIR)
while true do
    if hold ~= nil then
        if hold.frames > 0 then
            joypad.set(hold.buttons)
            if hold.analog then
                joypad.setanalog(hold.analog)
            end
            hold.frames = hold.frames - 1
        elseif hold.release > 0 then
            hold.release = hold.release - 1
        else
            hold = nil
        end
    elseif waiting > 0 then
        waiting = waiting - 1
    elseif current_id == nil and emu.framecount() % POLL_EVERY == 0 then
        poll()
    end
    run_queue()
    emu.frameadvance()
end
