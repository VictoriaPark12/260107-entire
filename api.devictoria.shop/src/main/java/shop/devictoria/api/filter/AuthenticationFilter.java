package shop.devictoria.api.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * Proxy 패턴 - 인증 필터
 * 보호된 엔드포인트에 대한 인증 검증
 */
@Slf4j
@Component
public class AuthenticationFilter implements GlobalFilter, Ordered {

    // 인증이 필요 없는 경로들
    private static final String[] PUBLIC_PATHS = {
            "/api/auth/",
            "/oauth2/",
            "/actuator/",
            "/api/ml/",
            "/api/titanic/",
            "/openapi.json",
            "/api/ml/openapi.json",
            "/api/ml/docs",
            "/docs",
            "/redoc",
            "/nlp/",
            "/samsung/",
            "/us_map/",
            "/seoul_map/",
            "/swagger-ui/",
            "/v3/api-docs/"
    };

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        // 공개 경로는 인증 검증 생략
        if (isPublicPath(path)) {
            return chain.filter(exchange);
        }

        // Authorization 헤더 확인
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (!StringUtils.hasText(authHeader) || !authHeader.startsWith("Bearer ")) {
            log.warn("[Auth Filter] 인증 토큰이 없습니다: {}", path);
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }

        // 토큰 추출 및 검증 로직은 여기에 추가 가능
        String token = authHeader.substring(7);
        log.debug("[Auth Filter] 토큰 확인: {}", token.substring(0, Math.min(20, token.length())) + "...");

        return chain.filter(exchange);
    }

    private boolean isPublicPath(String path) {
        for (String publicPath : PUBLIC_PATHS) {
            if (path.startsWith(publicPath)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public int getOrder() {
        // ProxyFilter 다음에 실행
        return 0;
    }
}

