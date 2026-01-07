package shop.devictoria.api.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "kakao")
public class KakaoProperties {
    private String restApiKey;
    private String adminKey;
    private String redirectUri;
    private String frontendUrl;
    private String tokenUri;
    private String userInfoUri;
}

