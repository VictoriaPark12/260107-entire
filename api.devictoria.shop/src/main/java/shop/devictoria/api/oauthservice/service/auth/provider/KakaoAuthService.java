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
import shop.devictoria.api.config.KakaoProperties;
import shop.devictoria.api.dto.auth.provider.KakaoTokenResponse;
import shop.devictoria.api.dto.auth.provider.KakaoUserInfo;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class KakaoAuthService {
    
    private final KakaoProperties kakaoProperties;
    private final WebClient.Builder webClientBuilder;
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * 카카오 인증 코드로 토큰 요청
     */
    public KakaoTokenResponse getKakaoToken(String authorizationCode) {
        System.out.println("[KakaoAuthService] 카카오 토큰 요청 시작");
        System.out.println("[KakaoAuthService] 인증 코드: " + authorizationCode);
        System.out.println("[KakaoAuthService] REST API Key: " + kakaoProperties.getRestApiKey());
        System.out.println("[KakaoAuthService] Redirect URI: " + kakaoProperties.getRedirectUri());
        System.out.println("[KakaoAuthService] Token URI: " + kakaoProperties.getTokenUri());
        
        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("grant_type", "authorization_code");
        formData.add("client_id", kakaoProperties.getRestApiKey());
        formData.add("redirect_uri", kakaoProperties.getRedirectUri());
        formData.add("code", authorizationCode);
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[KakaoAuthService] 카카오 API에 토큰 요청 전송 중...");
            KakaoTokenResponse response = webClient.post()
                    .uri(kakaoProperties.getTokenUri())
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .bodyValue(formData)
                    .retrieve()
                    .bodyToMono(KakaoTokenResponse.class)
                    .block();
            
            System.out.println("[KakaoAuthService] 카카오 토큰 요청 성공!");
            System.out.println("[KakaoAuthService] 받은 Access Token: " + (response.getAccessToken() != null ? response.getAccessToken().substring(0, Math.min(20, response.getAccessToken().length())) + "..." : "null"));
            return response;
            
        } catch (Exception e) {
            System.out.println("[KakaoAuthService] 카카오 토큰 요청 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("카카오 토큰 요청 실패", e);
        }
    }
    
    /**
     * 카카오 액세스 토큰으로 사용자 정보 조회
     */
    public KakaoUserInfo getKakaoUserInfo(String accessToken) {
        System.out.println("[KakaoAuthService] 카카오 사용자 정보 조회 시작");
        System.out.println("[KakaoAuthService] 사용할 Access Token: " + (accessToken != null ? accessToken.substring(0, Math.min(20, accessToken.length())) + "..." : "null"));
        System.out.println("[KakaoAuthService] User Info URI: " + kakaoProperties.getUserInfoUri());
        
        try {
            WebClient webClient = webClientBuilder.build();
            
            System.out.println("[KakaoAuthService] 카카오 API에 사용자 정보 요청 전송 중...");
            KakaoUserInfo userInfo = webClient.get()
                    .uri(kakaoProperties.getUserInfoUri())
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                    .retrieve()
                    .bodyToMono(KakaoUserInfo.class)
                    .block();
            
            System.out.println("[KakaoAuthService] 카카오 사용자 정보 조회 성공!");
            System.out.println("[KakaoAuthService] 사용자 ID: " + userInfo.getId());
            if (userInfo.getKakaoAccount() != null) {
                System.out.println("[KakaoAuthService] 이메일: " + userInfo.getKakaoAccount().getEmail());
                if (userInfo.getKakaoAccount().getProfile() != null) {
                    System.out.println("[KakaoAuthService] 닉네임: " + userInfo.getKakaoAccount().getProfile().getNickname());
                }
            }
            return userInfo;
            
        } catch (Exception e) {
            System.out.println("[KakaoAuthService] 카카오 사용자 정보 조회 실패: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("카카오 사용자 정보 조회 실패", e);
        }
    }
    
    /**
     * 인증 코드로 카카오 로그인 처리 (토큰 요청 + 사용자 정보 조회)
     */
    public KakaoUserInfo loginWithAuthorizationCode(String authorizationCode) {
        System.out.println("[KakaoAuthService] 인증 코드로 로그인 처리 시작");
        // 1. 인증 코드로 토큰 요청
        KakaoTokenResponse tokenResponse = getKakaoToken(authorizationCode);
        
        // 2. 토큰으로 사용자 정보 조회
        KakaoUserInfo userInfo = getKakaoUserInfo(tokenResponse.getAccessToken());
        
        // 3. 카카오 토큰을 Redis에 저장
        saveKakaoTokenToRedis(userInfo.getId(), tokenResponse);
        
        return userInfo;
    }
    
    /**
     * 카카오 토큰을 Redis에 저장
     */
    private void saveKakaoTokenToRedis(Long userId, KakaoTokenResponse tokenResponse) {
        try {
            String key = "kakao:token:" + userId;
            String tokenJson = objectMapper.writeValueAsString(tokenResponse);
            
            // 카카오 액세스 토큰 만료 시간 설정 (초 단위를 밀리초로 변환)
            long expiration = tokenResponse.getExpiresIn() != null ? 
                tokenResponse.getExpiresIn() : 3600; // 기본 1시간
            
            redisTemplate.opsForValue().set(key, tokenJson, expiration, TimeUnit.SECONDS);
            
            System.out.println("========================================");
            System.out.println("[KakaoAuthService] ✅ 카카오 토큰을 Redis에 저장했습니다");
            System.out.println("[KakaoAuthService] Redis Key: " + key);
            System.out.println("[KakaoAuthService] 만료 시간: " + expiration + "초");
            System.out.println("[KakaoAuthService] 저장된 카카오 Access Token: " + 
                (tokenResponse.getAccessToken() != null ? tokenResponse.getAccessToken().substring(0, Math.min(20, tokenResponse.getAccessToken().length())) + "..." : "null"));
            System.out.println("[KakaoAuthService] 저장된 카카오 Refresh Token: " + 
                (tokenResponse.getRefreshToken() != null ? tokenResponse.getRefreshToken().substring(0, Math.min(20, tokenResponse.getRefreshToken().length())) + "..." : "null"));
            System.out.println("(이 토큰은 Redis에만 저장되고, 프론트엔드로는 반환되지 않습니다)");
            System.out.println("========================================");
        } catch (JsonProcessingException e) {
            System.out.println("[KakaoAuthService] Redis 저장 실패: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.out.println("[KakaoAuthService] Redis 저장 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 액세스 토큰으로 카카오 로그인 처리 (사용자 정보 조회만)
     */
    public KakaoUserInfo loginWithAccessToken(String accessToken) {
        System.out.println("[KakaoAuthService] 액세스 토큰으로 로그인 처리 시작");
        return getKakaoUserInfo(accessToken);
    }
}

