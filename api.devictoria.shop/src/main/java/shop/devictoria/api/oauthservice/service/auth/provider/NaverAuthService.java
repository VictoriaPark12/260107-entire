package shop.devictoria.api.service.auth.provider;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.client.WebClient;
import shop.devictoria.api.config.NaverProperties;
import shop.devictoria.api.dto.auth.provider.NaverTokenResponse;
import shop.devictoria.api.dto.auth.provider.NaverUserInfo;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class NaverAuthService {
    
    private final NaverProperties naverProperties;
    private final WebClient.Builder webClientBuilder;
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * 네이버 인증 코드로 토큰 요청
     */
    public NaverTokenResponse getNaverToken(String authorizationCode, String state) {
        System.out.println("[NaverAuthService] 네이버 토큰 요청 시작");
        System.out.println("[NaverAuthService] 인증 코드: " + authorizationCode);
        System.out.println("[NaverAuthService] State: " + (state != null ? state : "null"));
        System.out.println("[NaverAuthService] Client ID: " + naverProperties.getClientId());
        System.out.println("[NaverAuthService] Redirect URI: " + naverProperties.getRedirectUri());
        System.out.println("[NaverAuthService] Token URI: " + naverProperties.getTokenUri());
        
        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("grant_type", "authorization_code");
        formData.add("client_id", naverProperties.getClientId());
        formData.add("client_secret", naverProperties.getClientSecret());
        formData.add("redirect_uri", naverProperties.getRedirectUri());
        formData.add("code", authorizationCode);
        // 네이버는 state 파라미터가 필수이므로, 없으면 빈 문자열 사용
        formData.add("state", state != null ? state : "");
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[NaverAuthService] 네이버 API에 토큰 요청 전송 중...");
            NaverTokenResponse response = webClient.post()
                    .uri(naverProperties.getTokenUri())
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .bodyValue(formData)
                    .retrieve()
                    .bodyToMono(NaverTokenResponse.class)
                    .block();
            
            if (response.getError() != null) {
                System.out.println("[NaverAuthService] 네이버 토큰 요청 실패: " + response.getError() + " - " + response.getErrorDescription());
                throw new RuntimeException("네이버 토큰 요청 실패: " + response.getErrorDescription());
            }
            
            System.out.println("[NaverAuthService] 네이버 토큰 요청 성공!");
            System.out.println("[NaverAuthService] 받은 Access Token: " + (response.getAccessToken() != null ? response.getAccessToken().substring(0, Math.min(20, response.getAccessToken().length())) + "..." : "null"));
            return response;
            
        } catch (Exception e) {
            System.out.println("[NaverAuthService] 네이버 토큰 요청 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("네이버 토큰 요청 실패", e);
        }
    }
    
    /**
     * 네이버 액세스 토큰으로 사용자 정보 조회
     */
    public NaverUserInfo getNaverUserInfo(String accessToken) {
        System.out.println("[NaverAuthService] 네이버 사용자 정보 조회 시작");
        System.out.println("[NaverAuthService] 사용할 Access Token: " + (accessToken != null ? accessToken.substring(0, Math.min(20, accessToken.length())) + "..." : "null"));
        System.out.println("[NaverAuthService] User Info URI: " + naverProperties.getUserInfoUri());
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[NaverAuthService] 네이버 API에 사용자 정보 요청 전송 중...");
            NaverUserInfo userInfo = webClient.get()
                    .uri(naverProperties.getUserInfoUri())
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                    .retrieve()
                    .bodyToMono(NaverUserInfo.class)
                    .block();
            
            if (!"00".equals(userInfo.getResultCode())) {
                System.out.println("[NaverAuthService] 네이버 사용자 정보 조회 실패: " + userInfo.getMessage());
                throw new RuntimeException("네이버 사용자 정보 조회 실패: " + userInfo.getMessage());
            }
            
            System.out.println("[NaverAuthService] 네이버 사용자 정보 조회 성공!");
            if (userInfo.getResponse() != null) {
                System.out.println("[NaverAuthService] 사용자 ID: " + userInfo.getResponse().getId());
                System.out.println("[NaverAuthService] 이메일: " + userInfo.getResponse().getEmail());
                System.out.println("[NaverAuthService] 이름: " + userInfo.getResponse().getName());
                System.out.println("[NaverAuthService] 닉네임: " + userInfo.getResponse().getNickname());
            }
            return userInfo;
            
        } catch (Exception e) {
            System.out.println("[NaverAuthService] 네이버 사용자 정보 조회 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("네이버 사용자 정보 조회 실패", e);
        }
    }
    
    /**
     * 인증 코드로 네이버 로그인 처리 (토큰 요청 + 사용자 정보 조회)
     */
    public NaverUserInfo loginWithAuthorizationCode(String authorizationCode, String state) {
        System.out.println("[NaverAuthService] 인증 코드로 로그인 처리 시작");
        // 1. 인증 코드로 토큰 요청
        NaverTokenResponse tokenResponse = getNaverToken(authorizationCode, state);
        
        // 2. 토큰으로 사용자 정보 조회
        NaverUserInfo userInfo = getNaverUserInfo(tokenResponse.getAccessToken());
        
        // 3. 네이버 토큰을 Redis에 저장
        if (userInfo.getResponse() != null) {
            saveNaverTokenToRedis(userInfo.getResponse().getId(), tokenResponse);
        }
        
        return userInfo;
    }
    
    /**
     * 네이버 토큰을 Redis에 저장
     */
    private void saveNaverTokenToRedis(String userId, NaverTokenResponse tokenResponse) {
        try {
            String key = "naver:token:" + userId;
            String tokenJson = objectMapper.writeValueAsString(tokenResponse);
            
            // 네이버 액세스 토큰 만료 시간 설정 (초 단위)
            long expiration = tokenResponse.getExpiresIn() != null ? 
                tokenResponse.getExpiresIn() : 3600; // 기본 1시간
            
            redisTemplate.opsForValue().set(key, tokenJson, expiration, TimeUnit.SECONDS);
            
            System.out.println("========================================");
            System.out.println("[NaverAuthService] ✅ 네이버 토큰을 Redis에 저장했습니다");
            System.out.println("[NaverAuthService] Redis Key: " + key);
            System.out.println("[NaverAuthService] 만료 시간: " + expiration + "초");
            System.out.println("[NaverAuthService] 저장된 네이버 Access Token: " + 
                (tokenResponse.getAccessToken() != null ? tokenResponse.getAccessToken().substring(0, Math.min(20, tokenResponse.getAccessToken().length())) + "..." : "null"));
            System.out.println("[NaverAuthService] 저장된 네이버 Refresh Token: " + 
                (tokenResponse.getRefreshToken() != null ? tokenResponse.getRefreshToken().substring(0, Math.min(20, tokenResponse.getRefreshToken().length())) + "..." : "null"));
            System.out.println("(이 토큰은 Redis에만 저장되고, 프론트엔드로는 반환되지 않습니다)");
            System.out.println("========================================");
        } catch (JsonProcessingException e) {
            System.out.println("[NaverAuthService] Redis 저장 실패: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.out.println("[NaverAuthService] Redis 저장 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 액세스 토큰으로 네이버 로그인 처리 (사용자 정보 조회만)
     */
    public NaverUserInfo loginWithAccessToken(String accessToken) {
        System.out.println("[NaverAuthService] 액세스 토큰으로 로그인 처리 시작");
        return getNaverUserInfo(accessToken);
    }
}

