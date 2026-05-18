import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  ArrowLeft,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { useState } from 'react';
import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form';
import { useFieldArray, useForm } from 'react-hook-form';
import { Link, useParams } from 'react-router-dom';
import { z } from 'zod';
import { Card } from '../components/ui/Card';
import { QueryErrorBlock, RefreshButton } from '../components/ui/QueryRefresh';
import { cn } from '../lib/cn';
import api from '../services/api';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';

const collectionFieldSchema = z.object({
  name: z.string().min(1, 'Field name is required'),
  type: z.string().min(1, 'Field type is required'),
});

const createCollectionSchema = z.object({
  collections: z.array(
    z.object({
      name: z
        .string()
        .min(1, 'Collection name is required')
        .regex(
          /^[a-zA-Z0-9_-]+$/,
          'Collection name can only contain letters, numbers, underscores, and hyphens'
        ),
      fields: z.array(collectionFieldSchema).min(1, 'At least one field is required'),
    })
  ).min(1, 'At least one collection is required'),
});

type CreateCollectionForm = z.infer<typeof createCollectionSchema>;

interface Collection {
  name: string;
  field_count: number;
  num_documents: number;
}

interface Database {
  database: {
    _id: string;
    user_id: string;
    displayName: string;
    dbName: string;
  };
  collections: Collection[];
  stats: {
    collection_count: number;
    total_fields: number;
  };
}

function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: number;
  hint: string;
}) {
  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-2)]/40 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-subtle)]">
        {label}
      </p>
      <p className="mt-2 text-3xl font-bold tabular-nums text-[var(--accent-bright)]">
        {value.toLocaleString()}
      </p>
      <p className="mt-2 text-xs text-[var(--text-muted)]">{hint}</p>
    </div>
  );
}

const DatabaseDetail = () => {
  const { dbId } = useParams<{ dbId: string }>();
  const queryClient = useQueryClient();
  const { refreshToken } = useAuthStore();
  const [isCreateCollectionModalOpen, setIsCreateCollectionModalOpen] = useState(false);

  const {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    refetch,
  } = useQuery<Database>({
    queryKey: ['database', dbId],
    queryFn: async () => api.get(`/core/api/v1/database/${dbId}`),
    enabled: !!refreshToken && !!dbId,
  });

  const isRefreshing = isFetching && !isLoading;

  const deleteMutation = useMutation({
    mutationFn: async ({ collection_name }: { collection_name: string }) => {
      await api.delete('/api/v2/drop_collections/', {
        database_id: dbId,
        collection_names: [collection_name],
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database', dbId] });
      toast.success('Collection deleted');
    },
    onError: () => {
      toast.error('Could not delete collection');
    },
  });

  const handleDelete = ({ collection_name }: { collection_name: string }) => {
    if (
      window.confirm(
        `Are you sure you want to delete "${collection_name}"? This action cannot be undone.`
      )
    ) {
      deleteMutation.mutate({ collection_name });
    }
  };

  const { register, control, handleSubmit, reset, formState: { errors } } =
    useForm<CreateCollectionForm>({
      resolver: zodResolver(createCollectionSchema),
      defaultValues: {
        collections: [{ name: '', fields: [{ name: '', type: '' }] }],
      },
    });

  const {
    fields: collections,
    append: appendCollection,
    remove: removeCollection,
  } = useFieldArray({
    control,
    name: 'collections',
  });

  const createCollectionsMutation = useMutation({
    mutationFn: async (formData: CreateCollectionForm) => {
      if (!dbId) throw new Error('Database ID is missing.');
      return api.post('/api/v2/add_collection/', {
        database_id: dbId,
        collections: formData.collections.map((col) => ({
          name: col.name,
          fields: col.fields.map((field) => ({
            name: field.name,
            type: field.type,
          })),
        })),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database', dbId] });
      setIsCreateCollectionModalOpen(false);
      reset();
      toast.success('Collections added');
    },
    onError: () => {
      toast.error('Could not add collections');
    },
  });

  const onSubmitCreateCollections = (formData: CreateCollectionForm) => {
    createCollectionsMutation.mutate(formData);
  };

  const refreshStats = () => void refetch();
  const refreshCollections = () => void refetch();

  if (isLoading && !data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-[var(--accent-bright)]" />
      </div>
    );
  }

  if (isError && !data) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 py-8">
        <Link
          to="/dashboard/overview"
          className="inline-flex items-center gap-2 text-sm font-medium text-[var(--accent-bright)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to overview
        </Link>
        <div className="rounded-[var(--radius-lg)] border border-[var(--danger-soft)] bg-[var(--danger-soft)]/30 px-6 py-10 text-center">
          <AlertCircle className="mx-auto mb-3 h-10 w-10 text-[var(--danger)]" />
          <p className="text-[var(--text-primary)]">Could not load this database.</p>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {(error as Error)?.message || 'Check your connection and try again.'}
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isRefreshing}
            className="mt-4 inline-flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            to="/dashboard/overview"
            className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-[var(--accent-bright)] transition-colors hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to overview
          </Link>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            {data?.database.displayName || 'Database'}
          </h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Collections and statistics for this database
            {isRefreshing && (
              <RefreshCw className="ml-2 inline h-3.5 w-3.5 animate-spin align-middle" />
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isRefreshing}
          className="inline-flex items-center gap-2 self-start rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-2)] disabled:opacity-50"
          aria-label="Refresh database details"
        >
          <RefreshCw className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
          Refresh
        </button>
      </div>

      <Card
        title="Database statistics"
        action={
          <RefreshButton
            onClick={refreshStats}
            isRefreshing={isRefreshing}
            label="Reload stats"
          />
        }
      >
        {isError ? (
          <QueryErrorBlock
            message="Failed to load statistics."
            onRetry={refreshStats}
            isRefreshing={isRefreshing}
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <StatTile
              label="Collections"
              value={data?.stats.collection_count ?? 0}
              hint="Total collections in this database"
            />
            <StatTile
              label="Fields defined"
              value={data?.stats.total_fields ?? 0}
              hint="Sum of schema fields across collections"
            />
          </div>
        )}
      </Card>

      <Card
        title={`Collections in "${data?.database.displayName || 'this database'}"`}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <RefreshButton
              onClick={refreshCollections}
              isRefreshing={isRefreshing}
              label="Reload list"
            />
            <button
              type="button"
              onClick={() => setIsCreateCollectionModalOpen(true)}
              className="rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              aria-label="Add new collection"
            >
              Add collection
            </button>
          </div>
        }
      >
        {isError ? (
          <QueryErrorBlock
            message="Failed to load collections."
            onRetry={refreshCollections}
            isRefreshing={isRefreshing}
          />
        ) : (
          <div className={cn('overflow-x-auto', isRefreshing && 'opacity-70')}>
            <table className="min-w-full table-auto text-sm">
              <thead>
                <tr className="border-b border-[var(--border-subtle)] text-left text-[var(--text-subtle)]">
                  <th className="p-3 font-semibold">Collection</th>
                  <th className="p-3 font-semibold">Fields</th>
                  <th className="p-3 font-semibold">Documents</th>
                  <th className="p-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.collections?.length ? (
                  data.collections.map((collection) => (
                    <tr
                      key={collection.name}
                      className="border-b border-[var(--border-subtle)] transition-colors hover:bg-[var(--surface-2)]/50"
                    >
                      <td className="p-3 font-medium text-[var(--text-primary)]">
                        {collection.name}
                      </td>
                      <td className="p-3 text-[var(--text-muted)]">
                        {collection.field_count}
                      </td>
                      <td className="p-3 text-[var(--text-muted)]">
                        {collection.num_documents}
                      </td>
                      <td className="p-3">
                        <Link
                          to={`/dashboard/database/${dbId}/collection/${collection.name}`}
                          className="mr-4 font-medium text-[var(--accent-bright)] hover:underline"
                        >
                          View documents
                        </Link>
                        <button
                          type="button"
                          onClick={() =>
                            handleDelete({ collection_name: collection.name })
                          }
                          className="font-medium text-[var(--danger)] hover:underline"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={4}
                      className="p-8 text-center text-[var(--text-muted)]"
                    >
                      No collections yet. Add one to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <section className="rounded-[var(--radius-lg)] border border-red-700/50 bg-[var(--surface-1)] p-6">
        <h2 className="mb-4 text-lg font-semibold text-[var(--danger)]">Danger zone</h2>
        <div className="rounded-[var(--radius-md)] border border-red-700/40 bg-red-950/20 p-5">
          <p className="mb-4 text-sm text-[var(--text-muted)]">
            Delete this database permanently. All collections and documents will be lost.
          </p>
          <button
            type="button"
            disabled
            className="rounded-[var(--radius-md)] bg-[var(--danger)] px-6 py-2.5 text-sm font-semibold text-white opacity-50"
            aria-label="Delete database"
          >
            Delete database
          </button>
        </div>
      </section>

      {isCreateCollectionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/60 p-4">
          <div className="relative mx-auto w-full max-w-2xl rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 shadow-2xl sm:p-8">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
                Add new collection(s)
              </h2>
              <button
                type="button"
                onClick={() => setIsCreateCollectionModalOpen(false)}
                className="text-2xl text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
                aria-label="Close form"
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleSubmit(onSubmitCreateCollections)} className="space-y-6">
              <div>
                {errors.collections && (
                  <p className="mb-3 text-sm text-[var(--danger)]">
                    {errors.collections.message}
                  </p>
                )}
                <div className="space-y-4">
                  {collections.map((collection, index) => (
                    <div
                      key={collection.id}
                      className="relative rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-2)]/40 p-5"
                    >
                      <label
                        htmlFor={`collections.${index}.name`}
                        className="mb-2 block text-sm font-medium text-[var(--text-primary)]"
                      >
                        Collection name <span className="text-[var(--danger)]">*</span>
                      </label>
                      <input
                        id={`collections.${index}.name`}
                        {...register(`collections.${index}.name`)}
                        placeholder="e.g. users"
                        className="mb-3 w-full rounded-md border border-[var(--border-subtle)] bg-[var(--surface-0)] p-2 text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
                      />
                      {errors.collections?.[index]?.name && (
                        <p className="mb-3 text-sm text-[var(--danger)]">
                          {errors.collections[index].name?.message}
                        </p>
                      )}

                      <h4 className="mb-2 text-sm font-medium text-[var(--text-primary)]">
                        Fields for &quot;{collection.name || 'new collection'}&quot;{' '}
                        <span className="text-[var(--danger)]">*</span>
                      </h4>
                      {errors.collections?.[index]?.fields && (
                        <p className="mb-3 text-sm text-[var(--danger)]">
                          {errors.collections[index].fields?.message}
                        </p>
                      )}

                      <CollectionFields
                        collectionIndex={index}
                        control={control}
                        register={register}
                        errors={errors}
                      />

                      <button
                        type="button"
                        onClick={() => removeCollection(index)}
                        className="absolute right-3 top-3 text-[var(--text-muted)] transition-colors hover:text-[var(--danger)]"
                        aria-label="Remove collection"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() =>
                    appendCollection({ name: '', fields: [{ name: '', type: '' }] })
                  }
                  className="mt-4 flex items-center gap-1 font-medium text-[var(--accent-bright)] hover:underline"
                >
                  + Add another collection
                </button>
              </div>

              <div className="mt-8 flex justify-end gap-4 border-t border-[var(--border-subtle)] pt-6">
                <button
                  type="button"
                  onClick={() => setIsCreateCollectionModalOpen(false)}
                  className="rounded-md px-5 py-2.5 text-sm font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCollectionsMutation.isPending}
                  className="rounded-md bg-[var(--accent)] px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  {createCollectionsMutation.isPending ? 'Adding…' : 'Add collection(s)'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseDetail;

interface CollectionFieldsProps {
  collectionIndex: number;
  control: Control<CreateCollectionForm>;
  register: UseFormRegister<CreateCollectionForm>;
  errors: FieldErrors<CreateCollectionForm>;
}

const CollectionFields: React.FC<CollectionFieldsProps> = ({
  collectionIndex,
  control,
  register,
  errors,
}) => {
  const {
    fields: fieldArrayFields,
    append: appendField,
    remove: removeField,
  } = useFieldArray({
    control,
    name: `collections.${collectionIndex}.fields`,
  });

  return (
    <div className="space-y-2">
      {fieldArrayFields.map((field, fieldIndex) => (
        <div key={field.id} className="flex items-center gap-2">
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.name`)}
            placeholder="Field name"
            className="flex-grow rounded-md border border-[var(--border-subtle)] bg-[var(--surface-0)] p-2 text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:outline-none"
          />
          <input
            {...register(`collections.${collectionIndex}.fields.${fieldIndex}.type`)}
            placeholder="Field type"
            className="flex-grow rounded-md border border-[var(--border-subtle)] bg-[var(--surface-0)] p-2 text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] focus:border-[var(--accent)] focus:outline-none"
          />
          <button
            type="button"
            onClick={() => removeField(fieldIndex)}
            className="p-1 text-[var(--text-muted)] hover:text-[var(--danger)]"
            aria-label="Remove field"
          >
            &times;
          </button>
        </div>
      ))}
      {typeof errors.collections?.[collectionIndex]?.fields?.message === 'string' && (
        <p className="mt-1 text-sm text-[var(--danger)]">
          {errors.collections[collectionIndex].fields?.message}
        </p>
      )}
      <button
        type="button"
        onClick={() => appendField({ name: '', type: '' })}
        className="mt-2 font-medium text-[var(--accent-bright)] hover:underline"
      >
        + Add field
      </button>
    </div>
  );
};
