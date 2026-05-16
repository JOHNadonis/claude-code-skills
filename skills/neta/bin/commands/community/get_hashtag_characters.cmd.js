import z from "zod";
import { parseMeta } from "../../utils/parse_meta.js";
import { createCommand } from "../factory.js";
import { fetchCharactersByHashtagV1Parameters, fetchCharactersByHashtagV1ResultSchema, } from "../schema.js";
const meta = parseMeta(z.object({
    name: z.string(),
    title: z.string(),
    description: z.string(),
}), import.meta);
export const getHashtagCharacters = createCommand({
    name: meta.name,
    title: meta.title,
    description: meta.description,
    inputSchema: fetchCharactersByHashtagV1Parameters,
    outputSchema: fetchCharactersByHashtagV1ResultSchema,
}, async ({ hashtag, page_index, page_size, sort_by, parent_type }, { log, apis }) => {
    log.debug("get_hashtag_characters: hashtag: %s, page_index: %d, page_size: %d, sort_by: %s, parent_type: %s", hashtag, page_index, page_size, sort_by, parent_type);
    const result = await apis.hashtag.fetchCharactersByHashtag(hashtag, {
        page_index,
        page_size,
        sort_by,
        parent_type,
    });
    const simplifiedList = result.list.map((char) => ({
        uuid: char.uuid,
        name: char.name,
        short_name: char.short_name,
        avatar_img: char.config?.avatar_img || null,
        ctime: char.ctime,
        creator_uuid: char.creator?.uuid,
        creator_name: char.creator?.nick_name,
    }));
    return {
        total: result.total,
        page_index: result.page_index,
        page_size: result.page_size,
        list: simplifiedList,
        has_next: result.has_next,
    };
});
