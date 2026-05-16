import z from "zod";
import { parseMeta } from "../../utils/parse_meta.js";
import { createCommand } from "../factory.js";
import { fetchHashtagV1Parameters, fetchHashtagV1ResultSchema, } from "../schema.js";
const meta = parseMeta(z.object({
    name: z.string(),
    title: z.string(),
    description: z.string(),
}), import.meta);
export const getHashtagInfo = createCommand({
    name: meta.name,
    title: meta.title,
    description: meta.description,
    inputSchema: fetchHashtagV1Parameters,
    outputSchema: fetchHashtagV1ResultSchema,
}, async ({ hashtag }, { log, apis }) => {
    log.debug("get_hashtag_info: hashtag: %s", hashtag);
    const result = await apis.hashtag.fetchHashtag(hashtag);
    // 转换API返回结果为工具输出格式
    const activityDetail = result["activity_detail"];
    const simplifiedActivityDetail = activityDetail
        ? {
            uuid: activityDetail.uuid,
            title: activityDetail.title,
            banner_pic: activityDetail.banner_pic,
            creator_name: activityDetail.creator_name,
            review_users: activityDetail.review_users?.map((user) => ({
                uuid: user.uuid,
                name: user.name,
            })),
        }
        : undefined;
    const simplifiedHashtag = {
        name: result.name,
        lore: result.lore || [],
        activity_detail: simplifiedActivityDetail,
        hashtag_heat: result["hashtag_heat"],
        subscribe_count: result["subscribe_count"],
    };
    return {
        hashtag: simplifiedHashtag,
    };
});
