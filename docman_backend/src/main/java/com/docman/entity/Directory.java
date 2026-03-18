package docman.entity;

import lombok.Data;

@Data
public class Directory {
    private String directoryId;
    private String directoryName;
    private String indexName;
    private String type;
    private String createdAt;
}
