package api

import (
	"github.com/browserwing/browserwing/pkg/logger"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// TraceIDMiddleware 为每个请求生成 trace_id
func TraceIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 尝试从请求头获取 trace_id，如果没有则生成新的
		traceID := c.GetHeader("X-Trace-ID")
		if traceID == "" {
			traceID = uuid.New().String()
		}

		// 将 trace_id 存入 context
		ctx := logger.WithTraceID(c.Request.Context(), traceID)
		c.Request = c.Request.WithContext(ctx)

		// 将 trace_id 添加到响应头
		c.Header("X-Trace-ID", traceID)

		c.Next()
	}
}
