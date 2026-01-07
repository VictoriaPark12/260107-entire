package shop.devictoria.api;

import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * Gateway 테스트
 * 
 * JPA는 실제 데이터베이스 연결이 필요하므로 테스트에서는 제외합니다.
 */
@SpringBootTest(exclude = {
		DataSourceAutoConfiguration.class,
		HibernateJpaAutoConfiguration.class
})
class ApiApplicationTests {

	@Test
	void contextLoads() {
	}

}
