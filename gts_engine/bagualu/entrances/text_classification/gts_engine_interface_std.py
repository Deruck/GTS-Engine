from typing import Type, List, Optional, Dict
from pydantic import BaseModel, DirectoryPath, FilePath
from pathlib import Path

from ...lib.framework.base_gts_engine_interface import TRAIN_MODE, BaseGtsEngineInterface, GtsEngineArgs
from ...lib.utils.json import dump_json, load_json

from .training_pipeline_std import TrainingPipelineClfStd
from .inference_engine_std import InferenceEngineClfStd


class TypeCheckedTrainArgs(BaseModel):
    """GTS-Engine相关参数进行runtime类型检查与转换"""
    task_dir: DirectoryPath
    pretrained_model_dir: DirectoryPath
    data_dir: DirectoryPath
    save_path: DirectoryPath
    train_data_path: FilePath
    valid_data_path: FilePath
    test_data_path: Optional[FilePath]
    label_data_path: Optional[FilePath]
    gpus: int
    train_mode: TRAIN_MODE
    seed: int
    
class TypeCheckedInfArgs(BaseModel):
    model_save_dir: DirectoryPath
    label2id_path: FilePath
    
class GtsEngineInterfaceClfStd(BaseGtsEngineInterface):
    
    @property
    def _training_pipeline_cls(self):
        return TrainingPipelineClfStd
    
    def _parse_training_args(self, args: GtsEngineArgs) -> List[str]:
        # args类型检查
        type_checked_args = TypeCheckedTrainArgs(
            task_dir=Path(args.task_dir),
            pretrained_model_dir=Path(args.pretrained_model_dir),
            data_dir=Path(args.data_dir),
            save_path=Path(args.save_path),
            train_data_path=args.train_data_path,
            valid_data_path=args.valid_data_path,
            test_data_path=args.test_data_path,
            label_data_path=self.__get_label2id_path(args), # 将在prepare_training()中通过label_data生成label2id.json
            gpus=args.gpus,
            train_mode=TRAIN_MODE(args.train_mode),
            seed=args.seed
        )
        args_parse_list: List[str] = []
        args_parse_list.extend(["--gts_input_path", str(type_checked_args.task_dir)])
        args_parse_list.extend(["--gts_pretrained_model_path", str(type_checked_args.pretrained_model_dir)])
        args_parse_list.extend(["--gts_output_dir", str(type_checked_args.save_path)])
        args_parse_list.extend(["--gts_train_level", "1"])
        args_parse_list.extend(["--gpu_num", str(type_checked_args.gpus)])
        args_parse_list.extend(["--run_mode", "online"])
        args_parse_list.extend(["--train_data_path", str(type_checked_args.train_data_path)])
        args_parse_list.extend(["--dev_data_path", str(type_checked_args.valid_data_path)])
        args_parse_list.extend(["--aug_eda_path", str(self.__get_eda_cache_path(args))])
        if type_checked_args.test_data_path is not None:
            args_parse_list.extend(["--test_data_path", str(type_checked_args.test_data_path)])
        try:
            assert type_checked_args.label_data_path is not None
            args_parse_list.extend(["--label2id_path", str(type_checked_args.label_data_path)])
        except:
            raise Exception("you should pass label_data file in classification task")
        args_parse_list.extend(["--log_dir", str(type_checked_args.task_dir / "logs")])
        return args_parse_list
    
    def prepare_training(self, args: GtsEngineArgs) -> None:
        # 将label_data数据转为label2id格式
        assert args.label_data_path is not None
        label_data: Dict[str, List[str]] = load_json(args.label_data_path) # type: ignore
        label2id = {
            label: {"id": idx, "label_desc_zh": label}
            for idx, label in enumerate(label_data["labels"])
        }
        dump_json(label2id, self.__get_label2id_path(args))
            
    @property
    def _inference_engine_cls(self):
        return InferenceEngineClfStd
    
    def _parse_inference_args(self, args: GtsEngineArgs) -> List[str]:
        type_checked_args = TypeCheckedInfArgs(
            label2id_path=self.__get_label2id_path(args),
            model_save_dir=Path(args.task_dir) / "outputs" / "student_output" / "finetune_output"
        )
        args_parse_list: List[str] = []
        args_parse_list.extend(["--model_save_dir", str(type_checked_args.model_save_dir)])
        args_parse_list.extend(["--label2id_path", str(type_checked_args.label2id_path)])
        return args_parse_list
        
    def __get_label2id_path(self, args: GtsEngineArgs) -> FilePath:
        return Path(args.task_dir) / f"{args.train_data.split('.')[0]}_label2id.json"
    
    def __get_eda_cache_path(self, args: GtsEngineArgs) -> FilePath:
        return Path(args.task_dir) / f"{args.train_data.split('.')[0]}_eda_augment.json"