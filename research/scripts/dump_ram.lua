-- Photo de la mémoire de DBZ: Attack of the Saiyans (BizHawk 2.11, cœur melonDS).
--
-- Ouvre une petite fenêtre : on tape une étiquette (ex. « avant_coffre1 ») et on clique « Prendre la photo ».
-- Le contenu complet du domaine « Main RAM » est alors écrit dans DUMP_DIR, sous le nom NN_etiquette.bin,
-- et une ligne est ajoutée à DUMP_DIR/index.txt (numéro ; étiquette ; image n° ; taille).
-- Le script ne fait que LIRE la mémoire du jeu.
--
-- Les photos contiennent des données du jeu : elles ne vont jamais dans Git.

local DUMP_DIR = "C:/Users/Aurelien/Desktop/archipelago/dbz_research/dumps/"
local DOMAIN = "Main RAM"
local CHUNK = 4096

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

local function take_photo(label)
    label = (label or ""):gsub("[^%w_%-]", "_")
    if label == "" then
        label = "sans_nom"
    end
    photo_number = photo_number + 1
    local name = string.format("%02d_%s.bin", photo_number, label)
    local size = memory.getmemorydomainsize(DOMAIN)
    local file, err = io.open(DUMP_DIR .. name, "wb")
    if file == nil then
        print("ERREUR : impossible d'écrire " .. DUMP_DIR .. name .. " (" .. tostring(err) .. ")")
        photo_number = photo_number - 1
        return
    end
    for address = 0, size - 1, CHUNK do
        local bytes = memory.read_bytes_as_array(address, math.min(CHUNK, size - address), DOMAIN)
        file:write(string.char(table.unpack(bytes)))
    end
    file:close()
    local index = io.open(DUMP_DIR .. "index.txt", "a")
    index:write(string.format("%02d;%s;%d;%d\n", photo_number, label, emu.framecount(), size))
    index:close()
    print(string.format("Photo %02d enregistrée : %s (%d octets, image n° %d)", photo_number, name, size, emu.framecount()))
end

-- Informations utiles pour la carte mémoire : liste des domaines et leur taille.
print("Domaines mémoire disponibles :")
for _, domain in pairs(memory.getmemorydomainlist()) do
    print(string.format("  %s : %d octets", domain, memory.getmemorydomainsize(domain)))
end
print(string.format("Photos déjà présentes : %d. Dossier : %s", photo_number, DUMP_DIR))

local ok, form = pcall(forms.newform, 320, 120, "Photo mémoire DBZ")
if not ok then
    print("La fenêtre n'a pas pu s'ouvrir : une seule photo est prise maintenant (relancer le script pour la suivante).")
    take_photo("photo")
    return
end
local label_box = forms.textbox(form, "", 180, 20, nil, 10, 10)
forms.button(form, "Prendre la photo", function() take_photo(forms.gettext(label_box)) end, 200, 8, 100, 24)
forms.label(form, "Étiquette (sans espace), puis clic.", 10, 45, 290, 20)
event.onexit(function() forms.destroy(form) end)

while true do
    emu.frameadvance()
end
