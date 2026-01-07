package shop.devictoria.api.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import shop.devictoria.api.config.JwtProperties;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class JwtTokenProvider {
    
    private final JwtProperties jwtProperties;
    
    private SecretKey getSigningKey() {
        String secret = jwtProperties.getSecret();
        
        // JWT_SECRET이 비어있거나 null인 경우 기본값 사용
        if (secret == null || secret.trim().isEmpty()) {
            System.out.println("[경고] JWT_SECRET이 설정되지 않았습니다. 기본 키를 사용합니다.");
            secret = "default-jwt-secret-key-for-development-only-change-in-production-32bytes";
        }
        
        byte[] keyBytes = secret.getBytes(StandardCharsets.UTF_8);
        
        // JWT는 최소 32바이트(256비트)가 필요
        // 키가 짧으면 반복해서 패딩
        if (keyBytes.length < 32) {
            System.out.println("[경고] JWT_SECRET이 너무 짧습니다 (" + keyBytes.length + "바이트). 32바이트로 패딩합니다.");
            byte[] paddedKey = new byte[32];
            // keyBytes.length가 0인 경우를 방지
            if (keyBytes.length == 0) {
                // 기본 바이트로 채움
                for (int i = 0; i < 32; i++) {
                    paddedKey[i] = (byte) (i % 256);
                }
            } else {
                for (int i = 0; i < 32; i++) {
                    paddedKey[i] = keyBytes[i % keyBytes.length];
                }
            }
            keyBytes = paddedKey;
        }
        
        return Keys.hmacShaKeyFor(keyBytes);
    }
    
    /**
     * Access Token 생성
     */
    public String createAccessToken(Long userId, String email, String nickname) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("email", email);
        claims.put("nickname", nickname);
        claims.put("type", "access");
        
        Date now = new Date();
        Date expiration = new Date(now.getTime() + jwtProperties.getAccessTokenExpiration());
        
        return Jwts.builder()
                .claims(claims)
                .subject(String.valueOf(userId))
                .issuedAt(now)
                .expiration(expiration)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * Refresh Token 생성
     */
    public String createRefreshToken(Long userId) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("type", "refresh");
        
        Date now = new Date();
        Date expiration = new Date(now.getTime() + jwtProperties.getRefreshTokenExpiration());
        
        return Jwts.builder()
                .claims(claims)
                .subject(String.valueOf(userId))
                .issuedAt(now)
                .expiration(expiration)
                .signWith(getSigningKey())
                .compact();
    }
    
    /**
     * 토큰 검증
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                    .verifyWith(getSigningKey())
                    .build()
                    .parseSignedClaims(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 토큰에서 Claims 추출
     */
    public Claims getClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
    
    /**
     * 토큰에서 사용자 ID 추출
     */
    public Long getUserId(String token) {
        Claims claims = getClaims(token);
        return claims.get("userId", Long.class);
    }
}

