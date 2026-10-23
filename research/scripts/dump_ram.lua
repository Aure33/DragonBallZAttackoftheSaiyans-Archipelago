-- Photo de la mémoire de DBZ: Attack of the Saiyans (BizHawk 2.11, cœur melonDS).
--
-- Lancer le script une fois (Lua Console). Ensuite, CHAQUE état de sauvegarde (Shift+F<n>) prend
-- automatiquement une photo : le contenu complet du domaine « Main RAM » est écrit dans DUMP_DIR
-- sous le nom NN.bin, et une ligne est ajoutée à DUMP_DIR/index.txt (numéro ; état ; image n° ; taille).
-- Le script ne fait que LIRE la mémoire du jeu.
--
-- Pourquoi pas directement les fichiers .State ? Le cœur melonDS n'y enregistre que les pages mémoire
-- modifiées depuis son démarrage, sans adresse simple : inutilisable pour une carte mémoire.
--
-- Les photos contiennent des données du jeu : elles ne vont jamais dans Git.

local DUMP_DIR = "C:/Users/Aurelien/Desktop/archipelago/dbz_research/dumps/"
local DOMAIN = "Main RAM"
local READ_SIZE = 65536 -- octets lus par appel à BizHawk
local WRITE_SIZE = 4096 -- octets convertis en texte d'un coup (limite de table.unpack)

local function count_existing_dumps()
    local index = io.open(DUMP_DIR .. "index.txt", "r")
    if index == nil then
        return 0
    end
    local count = 0
    for _ in index:lines() do
        count = count + 1
    end
    index:close()
    return count
end

local photo_number = count_existing_dumps()

local function take_photo(state_name)
    photo_number = photo_number + 1
    local name = string.format("%02d.bin", photo_number)
    local size = memory.getmemorydomainsize(DOMAIN)
    local file, err = io.open(DUMP_DIR .. name, "wb")
    if file == nil then
        print("ERREUR : impossible d'écrire " .. DUMP_DIR .. name .. " (" .. tostring(err) .. ")")
        photo_number = photo_number - 1
        return
    end
    for address = 0, size - 1, READ_SIZE do
        local bytes = memory.read_bytes_as_array(address, math.min(READ_SIZE, size - address), DOMAIN)
        for first = 1, #bytes, WRITE_SIZE do
            file:write(string.char(table.unpack(bytes, first, math.min(first + WRITE_SIZE - 1, #bytes))))
        end
    end
    file:close()
    local index = io.open(DUMP_DIR .. "index.txt", "a")
    index:write(string.format("%02d;%s;%d;%d\n", photo_number, tostring(state_name or ""), emu.framecount(), size))
    index:close()
    print(string.format("Photo %02d enregistrée (%d octets, image n° %d)", photo_number, size, emu.framecount()))
end

print("Domaines mémoire disponibles :")
for _, domain in pairs(memory.getmemorydomainlist()) do
    print(string.format("  %s : %d octets", domain, memory.getmemorydomainsize(domain)))
end
print(string.format("Photos déjà présentes : %d. Dossier : %s", photo_number, DUMP_DIR))
print("Prêt : chaque état de sauvegarde (Shift+F<n>) prendra une photo.")

event.onsavestate(take_photo, "photo_memoire")

while true do
    emu.frameadvance()
end
