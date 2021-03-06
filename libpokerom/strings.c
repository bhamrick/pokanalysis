/* vim: set et sw=4 sts=4: */

/*
 * Copyright © 2010-2011, Clément Bœsch
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
 * SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
 * OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
 * CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

#include "pokerom.h"

static char *alphabet[] = {
    [0x49] = "\n",      // pokédex desc sentence separator
    [0x4E] = "\n",      // pokédex desc normal \n
    [0x4F] = "\n",
    [0x51] = "\n\n",
    [0x54] = "POKé",
    [0x55] = "\n",      // stop with arrow indicator
    [0x57] = "",        // ending stop without arrow
    [0x5F] = "",        // pokémon cry?
    [0x7F] = " ",  [0x80] = "A",  [0x81] = "B",  [0x82] = "C",  [0x83] = "D", [0x84] = "E",
    [0x85] = "F",  [0x86] = "G",  [0x87] = "H",  [0x88] = "I",  [0x89] = "J", [0x8A] = "K",
    [0x8B] = "L",  [0x8C] = "M",  [0x8D] = "N",  [0x8E] = "O",  [0x8F] = "P", [0x90] = "Q",
    [0x91] = "R",  [0x92] = "S",  [0x93] = "T",  [0x94] = "U",  [0x95] = "V", [0x96] = "W",
    [0x97] = "X",  [0x98] = "Y",  [0x99] = "Z",  [0x9A] = "(",  [0x9B] = ")", [0x9C] = ":",
    [0x9D] = ";",  [0x9E] = "]",  [0x9F] = "[",  [0xA0] = "a",  [0xA1] = "b", [0xA2] = "c",
    [0xA3] = "d",  [0xA4] = "e",  [0xA5] = "f",  [0xA6] = "g",  [0xA7] = "h", [0xA8] = "i",
    [0xA9] = "j",  [0xAA] = "k",  [0xAB] = "l",  [0xAC] = "m",  [0xAD] = "n", [0xAE] = "o",
    [0xAF] = "p",  [0xB0] = "q",  [0xB1] = "r",  [0xB2] = "s",  [0xB3] = "t", [0xB4] = "u",
    [0xB5] = "v",  [0xB6] = "w",  [0xB7] = "x",  [0xB8] = "y",  [0xB9] = "z", [0xBA] = "é",
    [0xBB] = "'d", [0xBC] = "'l", [0xBD] = "'s", [0xBE] = "'t", [0xBF] = "'v",
    [0xE0] = "'",  [0xE1] = "PK", [0xE2] = "MN", [0xE3] = "-",  [0xE4] = "'r",
    [0xE5] = "'m", [0xE6] = "?",  [0xE7] = "!",  [0xE8] = ".",  [0xEF] = "♂",
    [0xF0] = "$",  [0xF1] = "x",  [0xF2] = ".",  [0xF3] = "/",  [0xF4] = ",", [0xF5] = "♀",
    [0xF6] = "0",  [0xF7] = "1",  [0xF8] = "2",  [0xF9] = "3",  [0xFA] = "4", [0xFB] = "5",
    [0xFC] = "6",  [0xFD] = "7",  [0xFE] = "8",  [0xFF] = "9"
};

char *get_pkmn_char(u8 c, char *def_ret)
{
    char *s = alphabet[c];
    return s ? s : def_ret;
}

void load_string(char *dest, u8 *src, size_t max_len, int fixed_str_len)
{
    int i, len;

    for (i = 0;; i += len) {
        char *insert = alphabet[(u8)*src++];

        if (!insert)
            break;
        len = strlen(insert);
        if ((fixed_str_len && i >= fixed_str_len) || (i + len >= (int)max_len))
            break;
        strcpy(&dest[i], insert);
    }
    dest[i] = 0;
}

PyObject *str_getbin(struct rom *self, PyObject *args)
{
    int i, j = 0;
    char *s, b[128];

    (void)self;
    for (PyArg_ParseTuple(args, "s", &s); *s && j < (int)sizeof(b) - 1; s++) {
        for (i = 0; i < (int)(sizeof(alphabet) / sizeof(*alphabet)); i++) {
            if (alphabet[i] && *alphabet[i] && strncmp(s, alphabet[i], strlen(alphabet[i])) == 0) {
                b[j++] = i;
                break;
            }
        }
    }
    b[j] = 0;
    return Py_BuildValue("s", b);
}

PyObject *str_getascii(struct rom *self, PyObject *args)
{
    int j = 0;
    char *s, b[128];

    (void)self;
    for (PyArg_ParseTuple(args, "s", &s); *s; s++) {
        char *insert = alphabet[(u8)*s];
        if (!insert)
            insert = "?";
        int len = strlen(insert);

        if (j + len > (int)sizeof(b) - 1)
            break;
        strcpy(&b[j], insert);
        j += len;
    }
    b[j] = 0;
    return Py_BuildValue("s", b);
}

static void load_packed_text_string(u8 *data, char *dst, u8 id, size_t max_len)
{
    while (--id) {
        while (*data != 0x50)
            data++;
        data++;
    }
    load_string(dst, data, max_len, 0);
}

#define TEXT_BASE_ADDR(b, i) &stream[ROM_ADDR((b), GET_ADDR(0x375d + ((i) - 1) * 2))]

void get_pkmn_name(u8 *stream, char *pname, u8 pkmn_id, size_t max_len)
{
    u8 *addr = TEXT_BASE_ADDR(0x07, 1) + 0x0A * (pkmn_id - 1);
    load_string(pname, addr, max_len, 10);
}

void get_item_name(u8 *stream, char *iname, u8 item_id, size_t max_len)
{
    if      (item_id > 250) snprintf(iname, 5, "HM%02d", item_id - 250);
    else if (item_id > 200) snprintf(iname, 5, "TM%02d", item_id - 200);
    else    load_packed_text_string(TEXT_BASE_ADDR(0x01, 4), iname, item_id, max_len);
}

void get_pkmn_move_name(u8 *stream, char *mname, u8 move_id, size_t max_len)
{
    load_packed_text_string(TEXT_BASE_ADDR(0x2c, 2), mname, move_id, max_len);
}

void get_trainer_name(u8 *stream, char *tname, u8 trainer_id, size_t max_len)
{
    load_packed_text_string(TEXT_BASE_ADDR(0x0e, 7), tname, trainer_id, max_len);
}
