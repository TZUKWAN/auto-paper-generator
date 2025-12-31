"""
统一错误处理模块

定义论文生成系统的标准异常类
"""


class PaperGenerationError(Exception):
    """基础异常 - 论文生成过程中的通用错误"""
    
    def __init__(self, message, stage=None, details=None):
        self.stage = stage
        self.details = details
        super().__init__(message)
    
    def __str__(self):
        base = super().__str__()
        if self.stage:
            base = f"[{self.stage}] {base}"
        return base


class APIError(PaperGenerationError):
    """API相关错误基类"""
    pass


class APIConnectionError(APIError):
    """API连接失败"""
    
    def __init__(self, provider, message="无法连接到API服务", details=None):
        self.provider = provider
        super().__init__(f"[{provider}] {message}", stage="API调用", details=details)


class APIRateLimitError(APIError):
    """API频率限制"""
    
    def __init__(self, provider, retry_after=60):
        self.retry_after = retry_after
        super().__init__(
            f"[{provider}] 触发频率限制，请在 {retry_after} 秒后重试",
            stage="API调用"
        )


class APIResponseError(APIError):
    """API响应错误"""
    
    def __init__(self, provider, status_code, message="API返回错误", details=None):
        self.status_code = status_code
        super().__init__(
            f"[{provider}] {message} (HTTP {status_code})",
            stage="API调用",
            details=details
        )


class ContentError(PaperGenerationError):
    """内容生成错误基类"""
    pass


class OutlineParseError(ContentError):
    """大纲解析失败"""
    
    def __init__(self, message="无法解析AI生成的大纲", raw_response=None):
        self.raw_response = raw_response
        super().__init__(message, stage="大纲生成")


class ContentTooShortError(ContentError):
    """生成内容过短"""
    
    def __init__(self, section_name, actual_length, expected_minimum=100):
        self.section_name = section_name
        self.actual_length = actual_length
        self.expected_minimum = expected_minimum
        super().__init__(
            f"'{section_name}' 生成内容过短 ({actual_length} 字符，期望至少 {expected_minimum})",
            stage="内容生成"
        )


class SectionGenerationError(ContentError):
    """章节生成失败"""
    
    def __init__(self, section_title, message="章节内容生成失败", details=None):
        self.section_title = section_title
        super().__init__(f"[{section_title}] {message}", stage="章节生成", details=details)


class ConfigurationError(PaperGenerationError):
    """配置错误"""
    
    def __init__(self, message, config_path=None):
        self.config_path = config_path
        super().__init__(message, stage="配置加载")


class LiteratureError(PaperGenerationError):
    """文献处理错误"""
    pass


class LiteraturePoolEmptyError(LiteratureError):
    """文献池为空"""
    
    def __init__(self, pool_path=None):
        self.pool_path = pool_path
        msg = "文献池为空或无法加载"
        if pool_path:
            msg += f": {pool_path}"
        super().__init__(msg, stage="文献加载")


class ExportError(PaperGenerationError):
    """导出错误"""
    
    def __init__(self, format_type, message="导出失败", details=None):
        self.format_type = format_type
        super().__init__(f"[{format_type}] {message}", stage="文件导出", details=details)
