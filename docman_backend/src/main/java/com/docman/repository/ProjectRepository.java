package docman.repository;

import docman.entity.ProjectDocument;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface ProjectRepository extends MongoRepository<ProjectDocument, String> {

}