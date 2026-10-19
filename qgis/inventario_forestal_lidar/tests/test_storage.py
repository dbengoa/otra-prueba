"""State I/O regressions; no real NAS is required."""
import errno
import json
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch,Mock
from inventario_forestal_lidar.storage import atomic_json,LASBlockReader
from inventario_forestal_lidar.core import Plot,Cancelled,AuthorizationRequired
from inventario_forestal_lidar.engine import Engine

class StorageTests(unittest.TestCase):
    def test_transient_missing_path_is_retried(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'estado.json';real=Path.replace;calls=[]
            def flaky(source,target):
                calls.append(source)
                if len(calls)<3:raise FileNotFoundError(errno.ENOENT,'share briefly unavailable',str(source))
                return real(source,target)
            with patch.object(Path,'replace',flaky):atomic_json(path,{'estado':'ok'},retry_delays=(0,0))
            self.assertEqual(json.loads(path.read_text()),{'estado':'ok'})
            self.assertEqual(len(calls),3);self.assertEqual(len(set(calls)),3)
            self.assertFalse(list(Path(d).glob('*.tmp')))
    def test_failed_replacement_preserves_previous_json(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'estado.json';atomic_json(path,{'old':1})
            with patch.object(Path,'replace',side_effect=OSError(errno.EIO,'network I/O')):
                with self.assertRaises(OSError):atomic_json(path,{'new':2},retry_delays=(0,0))
            self.assertEqual(json.loads(path.read_text()),{'old':1})
            self.assertFalse(list(Path(d).glob('*.tmp')))
    def test_missing_parent_is_not_recreated(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lost_share/estado.json'
            with self.assertRaises(FileNotFoundError):atomic_json(path,{},retry_delays=())
            self.assertFalse(path.parent.exists())
    def test_disk_full_is_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('inventario_forestal_lidar.storage.tempfile.NamedTemporaryFile',side_effect=OSError(errno.ENOSPC,'disk full')) as create:
                with self.assertRaises(OSError):atomic_json(Path(d)/'estado.json',{})
                self.assertEqual(create.call_count,1)
    def test_cancel_during_retry_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'estado.json';atomic_json(path,{'old':1});calls=0
            def check():
                nonlocal calls
                calls+=1
                if calls>=3:raise Cancelled('stop')
            with patch.object(Path,'replace',side_effect=OSError(errno.EIO,'network I/O')):
                with self.assertRaises(Cancelled):atomic_json(path,{'new':2},check,retry_delays=(.2,))
            self.assertEqual(json.loads(path.read_text()),{'old':1})
            self.assertFalse(list(Path(d).glob('*.tmp')))
    def test_concurrent_writers_use_different_temporaries(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'estado.json';barrier=threading.Barrier(2);real=Path.replace;temporaries=[]
            def simultaneous(source,target):
                temporaries.append(source);barrier.wait(timeout=5);return real(source,target)
            with patch.object(Path,'replace',simultaneous),ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(atomic_json,path,{'value':i}) for i in (1,2)]
                for future in futures:future.result(timeout=10)
            self.assertEqual(len(set(temporaries)),2)
            self.assertIn(json.loads(path.read_text())['value'],(1,2))
            self.assertFalse(list(Path(d).glob('*.tmp')))
    def broken_share(self,root):
        def write(path,data,**kwargs):
            if Path(path).is_relative_to(root/'share'):
                raise FileNotFoundError(errno.ENOENT,'share offline',str(path))
            return atomic_json(path,data,retry_delays=())
        return write
    def run_broken(self,root,engine,action):
        with patch('inventario_forestal_lidar.engine.diagnostic_root',return_value=root/'local'),patch('inventario_forestal_lidar.engine.atomic_json',side_effect=self.broken_share(root)),patch.object(engine,'_execute',side_effect=action):
            engine.execute()
    def test_processing_error_not_replaced_by_final_state_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=Engine({'output':str(root/'share'),'radius':15},[Plot('213.0',1,2)])
            with self.assertRaisesRegex(RuntimeError,'^original coverage failure$'):
                self.run_broken(root,e,ValueError('original coverage failure'))
            saved=json.loads(e.local_diagnostic_path.read_text())
            self.assertEqual(saved['error'],'original coverage failure');self.assertEqual(saved['status'],'failed')
            self.assertIn('state_storage_error',saved)
    def test_cancellation_and_authorization_survive_failed_final_write(self):
        for original in (Cancelled('stop'),AuthorizationRequired('official authorization pending')):
            with self.subTest(type=type(original).__name__),tempfile.TemporaryDirectory() as d:
                root=Path(d);e=Engine({'output':str(root/'share'),'radius':15},[Plot('213.0',1,2)])
                with self.assertRaises(type(original)) as caught:self.run_broken(root,e,original)
                self.assertIs(caught.exception,original)
                self.assertEqual(json.loads(e.local_diagnostic_path.read_text())['error'],str(original))
    def test_checkpoint_failure_stops_and_keeps_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=Engine({'output':str(root/'share'),'radius':15},[Plot('213.0',1,2)])
            with self.assertRaisesRegex(RuntimeError,'No se pudo guardar el estado'):
                self.run_broken(root,e,lambda output:e.phase('Comprobación de cobertura','213.0'))
            saved=json.loads(e.local_diagnostic_path.read_text())
            self.assertEqual(saved['status'],'failed');self.assertEqual(saved['active_plot'],'213.0')
    def test_success_is_not_reported_if_final_write_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=Engine({'output':str(root/'share'),'radius':15},[Plot('213.0',1,2)])
            with self.assertRaisesRegex(RuntimeError,'El cálculo terminó, pero'):
                self.run_broken(root,e,lambda output:None)
            saved=json.loads(e.local_diagnostic_path.read_text())
            self.assertEqual(saved['status'],'storage_error');self.assertEqual(saved['calculation_status'],'completed')
    def test_log_failure_uses_alternate_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=Engine({},[]);e.run=root/'share/run';e.logfile=e.run/'proceso.log'
            with patch('inventario_forestal_lidar.engine.diagnostic_root',return_value=root/'local'):e.log('primary error preserved')
            self.assertIn('primary error preserved',e.local_log_path.read_text())
    def test_both_logs_unavailable_do_not_raise(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=Engine({},[]);e.run=root/'share/run';e.logfile=e.run/'proceso.log'
            with patch.object(e,'diagnostics_directory',side_effect=OSError(errno.ENOSPC,'local disk full')):e.log('keep primary exception')
            self.assertIn('local_logging_error',e.state)

class LASReadTests(unittest.TestCase):
    def test_einval_reopens_and_retries_same_range(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.las';path.write_bytes(b'abcdefghij')
            real_open=open;handles=[];messages=[]
            def flaky_open(*args,**kwargs):
                handle=real_open(*args,**kwargs)
                proxy=Mock(wraps=handle)
                if not handles:proxy.read.side_effect=OSError(errno.EINVAL,'Invalid argument')
                handles.append(proxy);return proxy
            with patch('inventario_forestal_lidar.storage.open',side_effect=flaky_open,create=True):
                with LASBlockReader(path,progress=messages.append,retry_delays=(0,)) as reader:
                    self.assertEqual(reader.read_exact(2,4),b'cdef')
                    self.assertEqual(reader.read_exact(6,2),b'gh')
            self.assertEqual(len(handles),2)
            self.assertEqual(handles[0].seek.call_args.args,(2,))
            self.assertEqual(handles[1].seek.call_args_list[0].args,(2,))
            self.assertTrue(messages);self.assertEqual(path.read_bytes(),b'abcdefghij')
    def test_partial_range_is_discarded_before_retry(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.las';path.write_bytes(b'abcdefghij');real_open=open;handles=[]
            def flaky_open(*args,**kwargs):
                proxy=Mock(wraps=real_open(*args,**kwargs))
                if not handles:proxy.read.side_effect=[b'c',OSError(errno.EINVAL,'Invalid argument')]
                handles.append(proxy);return proxy
            with patch('inventario_forestal_lidar.storage.open',side_effect=flaky_open,create=True):
                with LASBlockReader(path,retry_delays=(0,)) as reader:
                    self.assertEqual(reader.read_exact(2,4),b'cdef')
            self.assertEqual(handles[1].seek.call_args.args,(2,))
    def test_read_error_preserves_errno_filename_and_offset(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.las';path.write_bytes(b'abcdefghij')
            with patch('inventario_forestal_lidar.storage.open',side_effect=OSError(errno.EINVAL,'Invalid argument'),create=True):
                with LASBlockReader(path,retry_delays=()) as reader:
                    with self.assertRaises(OSError) as caught:reader.read_exact(3,4)
            self.assertEqual(caught.exception.errno,errno.EINVAL)
            self.assertEqual(caught.exception.filename,str(path))
            self.assertIn('byte 3',str(caught.exception))
    def test_large_range_reads_are_bounded_and_exact(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.las';expected=b'x'*(2*1024*1024+7);path.write_bytes(expected)
            handle=open(path,'rb',buffering=0);proxy=Mock(wraps=handle)
            with patch('inventario_forestal_lidar.storage.open',return_value=proxy,create=True):
                with LASBlockReader(path) as reader:self.assertEqual(reader.read_exact(0,len(expected)),expected)
            self.assertTrue(all(call.args[0]<=1024*1024 for call in proxy.read.call_args_list))
    def test_metadata_retries_einval_without_altering_file(self):
        from fixtures import write_cloud
        from inventario_forestal_lidar.local import metadata,_metadata_once
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.las';write_cloud(path);before=path.read_bytes();original=_metadata_once
            calls=0
            def flaky(candidate):
                nonlocal calls
                calls+=1
                if calls==1:raise OSError(errno.EINVAL,'Invalid argument')
                return original(candidate)
            with patch('inventario_forestal_lidar.local._metadata_once',side_effect=flaky),patch('inventario_forestal_lidar.local.pause'):
                result=metadata(path)
            self.assertEqual(result.count,2);self.assertEqual(calls,2);self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':unittest.main()
