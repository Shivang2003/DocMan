package docman.dto;

import lombok.Data;

@Data
public class CreateDirectoryRequest {
    private String projectId;
    private String projectName;
    private String directoryName;
    private String indexName;
    private String type;
}