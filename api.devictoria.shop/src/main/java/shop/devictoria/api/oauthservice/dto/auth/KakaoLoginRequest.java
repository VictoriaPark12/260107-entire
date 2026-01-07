package shop.devictoria.api.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class KakaoLoginRequest {
    private String authorizationCode;
    private String accessToken;
    private String email;
    private String nickname;
}

