from synctypes import EnumMember, ModelExtractor, ModelTypes, TypeScriptWriter


class TestModelTypes:
    def test_has_content_with_constants(self):
        model = ModelTypes(model_name="Test", constants={"A_B": "value"})
        assert model.has_content is True

    def test_has_content_with_enums(self):
        model = ModelTypes(
            model_name="Test",
            enums={"TestEnum": [EnumMember("A", "a", "Label")]},
        )
        assert model.has_content is True

    def test_has_content_empty(self):
        model = ModelTypes(model_name="Test")
        assert model.has_content is False


class TestModelExtractor:
    def setup_method(self):
        self.extractor = ModelExtractor()

    def test_is_constant_valid(self):
        assert self.extractor._is_constant("STATUS_ACTIVE", "active") is True
        assert self.extractor._is_constant("PRIORITY_HIGH", 1) is True
        assert self.extractor._is_constant("RATE_LIMIT", 1.5) is True

    def test_is_constant_lowercase_rejected(self):
        assert self.extractor._is_constant("status_active", "active") is False

    def test_is_constant_no_underscore_rejected(self):
        assert self.extractor._is_constant("STATUS", "active") is False

    def test_is_constant_non_primitive_rejected(self):
        assert self.extractor._is_constant("STATUS_LIST", ["a", "b"]) is False

    def test_is_choices_tuple_valid_strings(self):
        choices = (("active", "Active"), ("inactive", "Inactive"))
        assert self.extractor._is_choices_tuple(choices) is True

    def test_is_choices_tuple_valid_ints(self):
        choices = ((1, "High"), (2, "Low"))
        assert self.extractor._is_choices_tuple(choices) is True

    def test_is_choices_tuple_list_format(self):
        choices = [["active", "Active"], ["inactive", "Inactive"]]
        assert self.extractor._is_choices_tuple(choices) is True

    def test_is_choices_tuple_empty_rejected(self):
        assert self.extractor._is_choices_tuple(()) is False
        assert self.extractor._is_choices_tuple([]) is False

    def test_is_choices_tuple_non_sequence_rejected(self):
        assert self.extractor._is_choices_tuple("string") is False
        assert self.extractor._is_choices_tuple(123) is False
        assert self.extractor._is_choices_tuple(None) is False

    def test_is_choices_tuple_wrong_inner_length_rejected(self):
        assert self.extractor._is_choices_tuple((("a", "b", "c"),)) is False

    def test_is_choices_tuple_non_string_label_rejected(self):
        assert self.extractor._is_choices_tuple(((1, 2),)) is False

    def test_to_enum_name_strips_choices(self):
        assert self.extractor._to_enum_name("STATUS_CHOICES") == "StatusEnum"
        assert self.extractor._to_enum_name("USER_TYPE_CHOICES") == "UserTypeEnum"

    def test_to_enum_name_strips_types(self):
        assert self.extractor._to_enum_name("STATUS_TYPES") == "StatusEnum"

    def test_to_enum_name_no_suffix(self):
        assert self.extractor._to_enum_name("STATUS") == "StatusEnum"
        assert self.extractor._to_enum_name("PRIORITY_LEVEL") == "PriorityLevelEnum"

    def test_value_to_name_string(self):
        assert self.extractor._value_to_name("active") == "ACTIVE"
        assert self.extractor._value_to_name("in-progress") == "IN_PROGRESS"
        assert self.extractor._value_to_name("some value") == "SOME_VALUE"

    def test_value_to_name_numeric(self):
        assert self.extractor._value_to_name(1) == "VALUE_1"
        assert self.extractor._value_to_name(42) == "VALUE_42"

    def test_extract_string_constants(self, mock_model):
        result = self.extractor.extract(mock_model)
        assert result.constants["STATUS_ACTIVE"] == "active"
        assert result.constants["STATUS_INACTIVE"] == "inactive"

    def test_extract_int_constants(self, mock_model):
        result = self.extractor.extract(mock_model)
        assert result.constants["PRIORITY_HIGH"] == 1
        assert result.constants["PRIORITY_LOW"] == 2

    def test_extract_enums(self, mock_model):
        result = self.extractor.extract(mock_model)
        assert "StatusEnum" in result.enums
        assert "PriorityEnum" in result.enums

    def test_extract_enum_members_use_constant_names(self, mock_model):
        result = self.extractor.extract(mock_model)
        member_names = [m.name for m in result.enums["StatusEnum"]]
        assert "STATUS_ACTIVE" in member_names
        assert "STATUS_INACTIVE" in member_names

    def test_extract_empty_model(self, mock_model_no_constants):
        result = self.extractor.extract(mock_model_no_constants)
        assert result.constants == {}
        assert result.enums == {}


class TestTypeScriptWriter:
    def test_write_file_creates_new(self, tmp_path):
        writer = TypeScriptWriter(tmp_path)
        writer._write_file("test.ts", "content")

        assert (tmp_path / "test.ts").read_text() == "content"
        assert str(tmp_path / "test.ts") in writer.changed

    def test_write_file_skips_unchanged(self, tmp_path):
        (tmp_path / "test.ts").write_text("content")
        writer = TypeScriptWriter(tmp_path)
        writer._write_file("test.ts", "content")

        assert writer.changed == []

    def test_write_file_updates_changed(self, tmp_path):
        (tmp_path / "test.ts").write_text("old content")
        writer = TypeScriptWriter(tmp_path)
        writer._write_file("test.ts", "new content")

        assert (tmp_path / "test.ts").read_text() == "new content"
        assert str(tmp_path / "test.ts") in writer.changed

    def test_write_file_dry_run(self, tmp_path):
        writer = TypeScriptWriter(tmp_path, dry_run=True)
        writer._write_file("test.ts", "content")

        assert not (tmp_path / "test.ts").exists()
        assert str(tmp_path / "test.ts") in writer.changed

    def test_write_file_creates_directories(self, tmp_path):
        nested = tmp_path / "nested" / "dir"
        writer = TypeScriptWriter(nested)
        writer._write_file("test.ts", "content")

        assert nested.exists()
        assert (nested / "test.ts").read_text() == "content"

    def test_write_constants(self, tmp_path):
        writer = TypeScriptWriter(tmp_path)
        models = [
            ModelTypes(
                model_name="User",
                constants={"STATUS_ACTIVE": "active", "PRIORITY_HIGH": 1},
            ),
        ]
        writer._write_constants(models)

        content = (tmp_path / "constants.ts").read_text()
        assert "export const User" in content
        assert 'STATUS_ACTIVE: "active"' in content
        assert "PRIORITY_HIGH: 1" in content
        assert "as const" in content

    def test_write_enums(self, tmp_path):
        writer = TypeScriptWriter(tmp_path)
        models = [
            ModelTypes(
                model_name="User",
                enums={
                    "StatusEnum": [
                        EnumMember("STATUS_ACTIVE", "active", "Active"),
                        EnumMember("STATUS_INACTIVE", "inactive", "Inactive"),
                    ]
                },
            ),
        ]
        writer._write_enums(models)

        content = (tmp_path / "enums.ts").read_text()
        assert "export enum UserStatusEnum" in content
        assert 'STATUS_ACTIVE = "active"' in content
        assert "// Active" in content

    def test_write_index(self, tmp_path):
        writer = TypeScriptWriter(tmp_path)
        writer._write_index()

        content = (tmp_path / "index.ts").read_text()
        assert 'export * from "./constants"' in content
        assert 'export * from "./enums"' in content

    def test_write_all_returns_changed(self, tmp_path):
        writer = TypeScriptWriter(tmp_path)
        models = [ModelTypes(model_name="User", constants={"STATUS_A": "a"})]
        changed = writer.write_all(models)

        assert len(changed) == 3
        assert any("constants.ts" in p for p in changed)
        assert any("enums.ts" in p for p in changed)
        assert any("index.ts" in p for p in changed)
